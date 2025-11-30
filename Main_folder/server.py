from flask import Flask, Response
import cv2
import time
from ultralytics import YOLO
from sus7withtele import PersonTrack  # import your class

app = Flask(__name__)

# ===============================
# YOLO Model and Video Setup
# ===============================
model = YOLO("yolov8n.pt")

# Use webcam (you can change to video file later)
cap = cv2.VideoCapture(0)
fps = cap.get(cv2.CAP_PROP_FPS) or 30

# Tracking setup
tracks = {}
next_id = 0

def generate_frames():
    global next_id
    while True:
        success, frame = cap.read()
        if not success:
            print("[!] Camera read failed, stopping stream.")
            break

        results = model(frame, classes=[0])  # detect persons only

        for box in results[0].boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)

            if next_id not in tracks:
                tracks[next_id] = PersonTrack(next_id, fps)
            track = tracks[next_id]
            track.update_flags((x1, y1, x2, y2), frame)
            suspicion = track.calculate_suspicion()

            # Draw overlays
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"ID {track.id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            color = (0, 255, 0) if suspicion < 50 else (0, 0, 255)
            behaviors_text = ", ".join(track.behavior_flags) if track.behavior_flags else "Normal"
            cv2.putText(frame, f"Suspicion: {suspicion}", (x1, y1 - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f"Behavior: {behaviors_text}", (x1, y1 - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()

        # Stream frames as MJPEG to frontend
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return "✅ Backend running — visit /video_feed to see the video stream."

if __name__ == "__main__":
    print("[+] Starting Flask video stream server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
