import subprocess
import sys
from flask import Flask, jsonify
import cv2
import time
from ultralytics import YOLO
from sus7withtele import PersonTrack
from flask import Response


model = None
cap = None
tracking_active = False
tracks = {}
next_id = 0
fps = 30



app = Flask(__name__)

sus_process = None  # Global process handle

# --------------------------------------------------
# START FUNCTION
# --------------------------------------------------
def run_sus():
    global sus_process

    if sus_process and sus_process.poll() is None:
        print("[server] sus7withtele.py is already running.")
        return False

    print("[server] Starting sus7withtele.py...")
    sus_process = subprocess.Popen([sys.executable, "sus7withtele.py"])
    print("[server] sus7withtele.py started.")
    return True


# --------------------------------------------------
# STOP FUNCTION
# --------------------------------------------------
def stop_sus():
    global sus_process

    if sus_process is None:
        print("[server] sus7withtele.py is not running.")
        return False

    if sus_process.poll() is not None:
        print("[server] sus7withtele.py already stopped.")
        sus_process = None
        return True

    print("[server] Stopping sus7withtele.py...")
    sus_process.terminate()
    sus_process = None
    print("[server] sus7withtele.py stopped.")
    return True


# --------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------

@app.route("/start", methods=["POST"])
def api_start():
    ok = run_sus()
    if ok:
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@app.route("/stop", methods=["POST"])
def api_stop():
    ok = stop_sus()
    if ok:
        return jsonify({"status": "stopped"})
    else:
        return jsonify({"status": "not_running"})


@app.route("/status", methods=["GET"])
def api_status():
    if sus_process and sus_process.poll() is None:
        return jsonify({"running": True})
    else:
        return jsonify({"running": False})





def generate_frames():
    global cap, model, next_id, tracks, tracking_active, fps

    while tracking_active:
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, classes=[0])  # persons only

        for box in results[0].boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)

            if next_id not in tracks:
                tracks[next_id] = PersonTrack(next_id, fps)

            track = tracks[next_id]
            track.update_flags((x1, y1, x2, y2), frame)
            suspicion = track.calculate_suspicion()

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"ID {track.id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            color = (0, 255, 0) if suspicion < 50 else (0, 0, 255)
            behaviors_text = ", ".join(track.behavior_flags) or "Normal"

            cv2.putText(frame, f"Suspicion: {suspicion}",
                        (x1, y1 - 40), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, color, 2)
            cv2.putText(frame, f"Behavior: {behaviors_text}",
                        (x1, y1 - 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')


@app.route("/feed")
def feed():
    global model, cap, tracking_active, fps, tracks, next_id

    # Auto-start logic
    if not tracking_active:
        print("[feed] Initializing YOLO and webcam...")

        model = YOLO("yolov8n.pt")
        cap = cv2.VideoCapture(0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        if not cap.isOpened():
            return "Camera failed to open", 500

        # Reset detection state
        tracks = {}
        next_id = 0
        tracking_active = True

        print("[feed] Webcam + YOLO started automatically.")

    # Start sending frames
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )




@app.route("/stop_feed", methods=["POST"])
def stop_feed():
    global tracking_active, cap
    tracking_active = False
    if cap:
        cap.release()
    return jsonify({"status": "feed_stopped"})




# --------------------------------------------------
# MAIN GUARD
# --------------------------------------------------
if __name__ == "__main__":
    print("[server] Flask API running on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000)
