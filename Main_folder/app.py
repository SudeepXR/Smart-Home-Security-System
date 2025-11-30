# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import time
import signal
import sys
from database.db import SessionLocal
from database.models import VisitorLog
from database.utils import create_user_secure
from database.utils import authenticate_user

from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import sys
import os




# Global handle to the twoway.py process
twoway_process = None

# Resolve absolute path to twoway.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TWOWAY_PATH = os.path.join(BASE_DIR, "twoway.py")


# --- CONFIG ---
SYSTEM_SCRIPT = os.path.join(os.path.dirname(__file__), "system_main.py")
# ----------------

app = Flask(__name__)
CORS(app)

_system_proc = None
_system_mode = None   # <<── track which mode system_main.py is running with


# -------------------------
# Process Control Functions
# -------------------------

def _start_system(mode=None):
    """Start system_main.py with optional --mode argument."""
    global _system_proc, _system_mode

    py = subprocess.sys.executable
    args = [py, SYSTEM_SCRIPT]

    if mode:
        args += ["--mode", mode]

    # Create process group to allow safe termination
    preexec_fn = None
    creationflags = 0
    if os.name != "nt":
        preexec_fn = os.setsid
    else:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    _system_proc = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=None,
        stderr=None,
        preexec_fn=preexec_fn,
        creationflags=creationflags
    )
    _system_mode = mode
    print(f"[app] Started system_main.py PID={_system_proc.pid} mode={_system_mode}")
    return _system_proc


def _stop_system(timeout=4.0):
    """Stop system_main.py cleanly, or kill if needed."""
    global _system_proc, _system_mode

    if _system_proc is None:
        _system_mode = None
        return True

    if _system_proc.poll() is not None:
        _system_proc = None
        _system_mode = None
        return True

    print("[app] Terminating system_main.py...")

    try:
        _system_proc.terminate()
    except:
        pass

    # wait up to timeout seconds
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _system_proc.poll() is not None:
            print("[app] system_main.py exited cleanly.")
            _system_proc = None
            _system_mode = None
            return True
        time.sleep(0.1)

    print("[app] Graceful terminate failed. Forcing kill...")

    try:
        if os.name != "nt":
            os.killpg(os.getpgid(_system_proc.pid), signal.SIGKILL)
        else:
            _system_proc.kill()
    except:
        pass

    if _system_proc.poll() is None:
        print("[app] ❌ Could NOT kill system_main.py")
        return False

    print("[app] system_main.py force-killed.")
    _system_proc = None
    _system_mode = None
    return True

def _handle_exit(signum, frame):
    print(f"[app] shutdown signal received ({signum}) — stopping child and exiting.")
    try:
        _stop_system(timeout=3.0)
    except Exception as e:
        print("[app] error while stopping child:", e)
    # flush and exit
    sys.stdout.flush()
    sys.exit(0)

# Register for SIGINT (Ctrl+C) and SIGTERM
if os.name != "nt":
    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)
else:
    # On Windows, SIGINT is fine. SIGTERM may not be available the same way.
    signal.signal(signal.SIGINT, _handle_exit)


# -------------------------
# API Route
# -------------------------

@app.route("/api/system/arm", methods=["POST"])
def arm_system():
    global _system_proc, _system_mode

    data = request.get_json(force=True, silent=True) or {}
    armed = bool(data.get("armed"))
    mode = data.get("mode")

    if isinstance(mode, str):
        mode = mode.strip().lower()
    else:
        mode = None

    print(f"[app] Request: armed={armed}, mode={mode}")

    # ARM
    if armed:
        # If running & same mode -> no action
        if _system_proc is not None and _system_proc.poll() is None:
            if mode == _system_mode:
                return jsonify({"status": "already_running", "mode": _system_mode}), 200
            
            # running but mode changed → restart
            print("[app] Restarting with new mode:", mode)
            _stop_system()

        # Start new (use the helper so creationflags / preexec_fn are applied consistently)
        _start_system(mode=mode)

        time.sleep(0.2)
        if _system_proc is not None and _system_proc.poll() is not None:
            return jsonify({"status": "error", "error": "process crashed"}), 500

        return jsonify({"status": "started", "mode": _system_mode}), 200

    # DISARM
    else:
        _stop_system()
        return jsonify({"status": "stopped"}), 200



@app.route("/api/system/status", methods=["GET"])
def status():
    running = _system_proc is not None and _system_proc.poll() is None
    pid = _system_proc.pid if running else None
    return jsonify({"running": running, "mode": _system_mode, "pid": pid})

@app.route("/api/visitors", methods=["GET"])
def get_visitors():
    """
    Returns all visitor logs as JSON for the frontend.
    """
    db = SessionLocal()
    try:
        logs = (
            db.query(VisitorLog)
            .order_by(VisitorLog.timestamp.desc())
            .all()
        )

        result = [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "name": log.name,
                "purpose": log.purpose,
            }
            for log in logs
        ]

        return jsonify(result), 200

    finally:
        db.close()

@app.route("/api/visitors/clear", methods=["POST"])
def clear_visitors():
    """
    Delete all visitor logs.
    Be careful – this wipes the table.
    """
    db = SessionLocal()
    try:
        deleted = db.query(VisitorLog).delete()
        db.commit()
        return jsonify({"status": "ok", "deleted": deleted}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        db.close()

@app.route("/api/users/create", methods=["POST"])
def api_create_user():
    """
    Create a new user IF house password is correct.
    Requires:
    - email
    - password
    - house_password
    """
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    house_password = data.get("house_password")

    if not email or not password or not house_password:
        return jsonify({"status": "error", "error": "Missing fields"}), 400

    user = create_user_secure(email, password, house_password)
    if user is None:
        return jsonify({"status": "error", "error": "Wrong house password"}), 403
    if user == "Existing":
        return jsonify({"status": "error", "error": "Existing user login"}), 403
    return jsonify({"status": "ok", "user_id": user.id}), 200

@app.route("/api/users/login", methods=["POST"])
def api_login_user():
    """
    Authenticate user by email + password.
    """
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "error": "Missing fields"}), 400

    user = authenticate_user(email, password)
    if user is None:
        return jsonify({"status": "error", "error": "Invalid credentials"}), 401

    return jsonify({
        "status": "ok",
        "user_id": user.id,
        "email": user.email,
    }), 200

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
    print(f"[app] Starting control API. system_main.py = {SYSTEM_SCRIPT}")
    app.run(host="0.0.0.0", port=5000, debug=True)
