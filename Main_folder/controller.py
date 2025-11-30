# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import sys
import os

app = Flask(__name__)

# Allow all origins for dev (including your http://localhost:3000)
CORS(app, resources={r"/": {"origins": ""}})

# Global handle to the twoway.py process
twoway_process = None

# Resolve absolute path to twoway.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TWOWAY_PATH = os.path.join(BASE_DIR, "twoway.py")


@app.route("/api/twoway/start", methods=["POST"])
def start_twoway():
    global twoway_process

    if twoway_process is not None and twoway_process.poll() is None:
        return jsonify({"status": "already_running"}), 400

    try:
        twoway_process = subprocess.Popen([sys.executable, TWOWAY_PATH])
        print("🎙 Started twoway.py")
        return jsonify({"status": "started"}), 200
    except Exception as e:
        print("Failed to start twoway.py:", e)
        twoway_process = None
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/twoway/stop", methods=["POST"])
def stop_twoway():
    global twoway_process

    if twoway_process is None or twoway_process.poll() is not None:
        twoway_process = None
        return jsonify({"status": "not_running"}), 400

    try:
        print("🛑 Stopping twoway.py...")
        twoway_process.terminate()
        twoway_process.wait(timeout=5)
        twoway_process = None
        return jsonify({"status": "stopped"}), 200
    except Exception as e:
        print("Error stopping twoway.py:", e)
        twoway_process = None
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    # If this is the dedicated twoway server, choose the port you actually use (8000 or 8008)
    app.run(host="0.0.0.0", port=8000, debug=True)
