from flask import Flask, Response
from flask_cors import CORS
import cv2

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

camera = cv2.VideoCapture(2)

if not camera.isOpened():
    raise RuntimeError("Camera not accessible")

def generate():
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        ret, jpeg = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpeg.tobytes() +
            b"\r\n"
        )

@app.route("/video")
def video():
    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/")
def health():
    return "Video backend running"

from waitress import serve

if __name__ == "__main__":
    serve(
        app,
        host="0.0.0.0",
        port=5001,
        threads=4
    )
