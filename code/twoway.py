import socket
import sounddevice as sd
import numpy as np
from collections import deque
import threading
import time
import os
from dotenv import load_dotenv

from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv(".env.local")

# ============ CONFIG ============
TARGET_IP = os.getenv("IP_COMM")   # change per laptop
PORT = 50005

RATE = 48000
BLOCK = 1920        # 40 ms (CRITICAL)
CHANNELS = 1

JITTER_BUFFER = 6
# ================================

# ============ FLASK ============
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# ===============================

# ============ AUDIO STATE ============
audio_running = False
audio_thread = None
audio_lock = threading.Lock()
# ====================================

def audio_loop():
    global audio_running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT))
    sock.setblocking(False)

    rx_buffer = deque(maxlen=JITTER_BUFFER)

    def net_recv():
        while audio_running:
            try:
                data, _ = sock.recvfrom(BLOCK * 2)
                rx_buffer.append(data)
            except BlockingIOError:
                time.sleep(0.001)

    threading.Thread(target=net_recv, daemon=True).start()

    def callback(indata, outdata, frames, time_info, status):
        if status:
            print(status)

        # SEND mic → peer
        sock.sendto(indata.tobytes(), (TARGET_IP, PORT))

        # PLAY received audio
        if rx_buffer:
            outdata[:] = np.frombuffer(
                rx_buffer.popleft(), dtype=np.int16
            ).reshape(-1, 1)
        else:
            outdata[:] = np.zeros((frames, 1), dtype=np.int16)

    with sd.Stream(
        samplerate=RATE,
        blocksize=BLOCK,
        channels=CHANNELS,
        dtype="int16",
        latency="high",
        callback=callback
    ):
        print("🎧 Audio communication STARTED")
        while audio_running:
            time.sleep(1)

    sock.close()
    print("🛑 Audio communication STOPPED")

# ============ API ROUTES ============

@app.route("/api/com/start", methods=["POST"])
def start_comm():
    global audio_thread, audio_running

    with audio_lock:
        if audio_running:
            return jsonify({
                "status": "already_running"
            }), 200

        audio_running = True
        audio_thread = threading.Thread(
            target=audio_loop,
            daemon=True
        )
        audio_thread.start()

    return jsonify({
        "status": "started"
    }), 200


@app.route("/api/com/stop", methods=["POST"])
def stop_comm():
    global audio_running

    with audio_lock:
        if not audio_running:
            return jsonify({
                "status": "not_running"
            }), 200

        audio_running = False

    return jsonify({
        "status": "stopped"
    }), 200


@app.route("/")
def health():
    return "✅ Comm server running"

# ============ MAIN ============
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )
