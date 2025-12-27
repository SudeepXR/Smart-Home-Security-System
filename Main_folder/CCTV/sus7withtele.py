import cv2
import time
import requests
from ultralytics import YOLO

# ===============================
# TELEGRAM SETUP
# ===============================
TELEGRAM_TOKEN = "8490718737:AAE5raIaK7z7aRB9TlEs7vK6M9xpvRVkles"
TELEGRAM_CHAT_ID = "6637316723"

def send_telegram_alert_with_video(flags, suspicion_index, video_file):
    message = f"⚠️ Suspicious Activity Detected!\nBehavior: {', '.join(flags)}\nSuspicion Index: {suspicion_index}"
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=5
        )
    except Exception as e:
        print(f"[!] Telegram text alert failed: {e}")

    try:
        with open(video_file, 'rb') as f:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo",
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"video": f},
                timeout=10
            )
    except Exception as e:
        print(f"[!] Telegram video alert failed: {e}")

# ===============================
# YOLO MODEL
# ===============================
model = YOLO("yolov8n.pt")  # lightweight for real-time detection

# ===============================
# PERSON TRACK CLASS
# ===============================
class PersonTrack:
    def __init__(self, pid, fps):
        print("HI")
        self.id = pid
        self.fps = fps
        self.behavior_flags = []
        self.behavior_start_time = {}
        self.suspicion_index = 0

        # Recording logic
        self.recording = False
        self.record_start_time = None
        self.clip_frames = []

        # Loitering / position tracking
        self.position_history = []
        self.stationary_start = None

        # Cooldown between alerts
        self.last_alert_time = 0
        self.alert_cooldown = 10  # seconds

    def update_flags(self, box, frame):
        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1
        flags = []

        # Track position for loitering
        center = ((x1 + x2)//2, (y1 + y2)//2)
        self.position_history.append(center)
        if len(self.position_history) > 30:
            self.position_history.pop(0)

        current_time = time.time()

        # -----------------
        # Crouching
        if 80 < h < 120:
            flags.append("Crouching")
            if "Crouching" not in self.behavior_start_time:
                self.behavior_start_time["Crouching"] = current_time

        # Climbing (top area)
        if y1 < 100:
            flags.append("Climbing")
            if "Climbing" not in self.behavior_start_time:
                self.behavior_start_time["Climbing"] = current_time

        # Crawling Entry (low height + horizontal movement)
        if h < 80 and len(self.position_history) >= 5:
            dx = max([c[0] for c in self.position_history]) - min([c[0] for c in self.position_history])
            if dx > 20:
                flags.append("Crawling Entry")
                if "Crawling Entry" not in self.behavior_start_time:
                    self.behavior_start_time["Crawling Entry"] = current_time

        # Loitering detection
        if len(self.position_history) >= 20:
            dx = max([c[0] for c in self.position_history]) - min([c[0] for c in self.position_history])
            dy = max([c[1] for c in self.position_history]) - min([c[1] for c in self.position_history])
            stationary_threshold = 20
            if dx < stationary_threshold and dy < stationary_threshold:
                if self.stationary_start is None:
                    self.stationary_start = current_time
                elif current_time - self.stationary_start >= 10:
                    flags.append("Loitering")
                    if "Loitering" not in self.behavior_start_time:
                        self.behavior_start_time["Loitering"] = self.stationary_start
            else:
                self.stationary_start = None

        self.behavior_flags = flags

        # -----------------
        # Start recording
        if self.behavior_flags and not self.recording:
            self.recording = True
            self.record_start_time = current_time
            self.clip_frames = []

        if self.recording:
            self.clip_frames.append(frame.copy())
            if current_time - self.record_start_time >= 25:  # 25s clip
                self.recording = False
                video_file = self.save_video_clip()

                # Send alert only if cooldown passed
                if current_time - self.last_alert_time >= self.alert_cooldown:
                    send_telegram_alert_with_video(
                        self.behavior_flags,
                        self.calculate_suspicion(),
                        video_file
                    )
                    self.last_alert_time = current_time

                # Reset flags after sending
                self.behavior_flags = []

    # Suspicion calculation
    def calculate_suspicion(self):
        suspicion = 0
        current_time = time.time()
        for behavior in self.behavior_flags:
            base = 30
            duration = current_time - self.behavior_start_time.get(behavior, current_time)
            suspicion += min(base + int(duration)*10, 100)
        return min(suspicion, 100)

    # Save recorded video clip
    def save_video_clip(self):
        if not self.clip_frames:
            return None
        filename = f"suspicious_{self.id}_{int(time.time())}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        height, width, _ = self.clip_frames[0].shape
        out = cv2.VideoWriter(filename, fourcc, int(self.fps), (width, height))
        for frame in self.clip_frames:
            out.write(frame)
        out.release()
        return filename


# ===============================
# MAIN LOOP (only runs if executed directly)
# ===============================
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    tracks = {}
    next_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, classes=[0])  # detect persons
        for box in results[0].boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)

            if next_id not in tracks:
                tracks[next_id] = PersonTrack(next_id, fps)
            track = tracks[next_id]

            track.update_flags((x1, y1, x2, y2), frame)
            suspicion = track.calculate_suspicion()

            # Draw bounding box and info
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"ID {track.id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            color = (0, 255, 0) if suspicion < 50 else (0, 0, 255)
            behaviors_text = ", ".join(track.behavior_flags) if track.behavior_flags else "Normal"
            cv2.putText(frame, f"Suspicion: {suspicion}", (x1, y1 - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f"Behavior: {behaviors_text}", (x1, y1 - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Security Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
