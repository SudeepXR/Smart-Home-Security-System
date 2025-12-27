from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import time
import signal
import signal
import sys
import google.generativeai as genai
import sys



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_SCRIPT = os.path.join(BASE_DIR, "two.py")
VIDEO_SCRIPT = os.path.join(BASE_DIR, "video.py")

# ==========================
# COMMUNICATION PROCESS STATE
# ==========================
audio_proc = None
video_proc = None




# ==========================
# GLOBAL SYSTEM STATE
# ==========================
_system_proc = None
_system_mode = None

#genai API CONFIG
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not set in environment")

genai.configure(api_key=api_key)


from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)


# ===== IMPORT DB UTILS =====
from database.utils import (
    create_user,
    authenticate_user,
    log_visitor,
    get_visitors_for_user,
    get_today_visitors_for_user,
    get_visitors_with_pics_for_user
)

# ==========================
# FLASK APP SETUP
# ==========================

app = Flask(__name__)

# JWT CONFIG
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-later"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # dev mode (no expiry)

jwt = JWTManager(app)


CORS(
    app,
    supports_credentials=True,
    resources={
        r"/*": {
            "origins": ["http://localhost:3000"]
        }
    }
)


def _start_communication():
    global audio_proc, video_proc

    # Already running
    if audio_proc is not None and audio_proc.poll() is None:
        return False, "already_running"

    py = sys.executable

    audio_proc = subprocess.Popen(
    [py, AUDIO_SCRIPT],
    stdin=subprocess.DEVNULL,
    stdout=None,
    stderr=None,
    close_fds=True
)

    video_proc = subprocess.Popen(
    [py, VIDEO_SCRIPT],
    stdin=subprocess.DEVNULL,
    stdout=None,
    stderr=None,
    close_fds=True
)


    time.sleep(0.5)

    # Check crashes
    if audio_proc.poll() is not None:
        audio_proc = None
        video_proc = None
        return False, "audio_failed"

    if video_proc.poll() is not None:
        audio_proc = None
        video_proc = None
        return False, "video_failed"

    return True, "started"


def _stop_communication(timeout=3.0):
    global audio_proc, video_proc

    # Nothing running → safe no-op
    if audio_proc is None and video_proc is None:
        return True

    procs = [audio_proc, video_proc]

    # Graceful stop
    for p in procs:
        if p and p.poll() is None:
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                else:
                    p.terminate()
            except:
                pass

    t0 = time.time()
    while time.time() - t0 < timeout:
        if all(p is None or p.poll() is not None for p in procs):
            audio_proc = None
            video_proc = None
            return True
        time.sleep(0.1)

    # Force kill
    for p in procs:
        try:
            if p and p.poll() is None:
                p.kill()
        except:
            pass

    audio_proc = None
    video_proc = None
    return True




# ==========================
# SIGNUP (CREATE USER)
# ==========================

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    doorbell_ip = data.get("doorbell_ip")
    cctv_ip = data.get("cctv_ip")
    file_destination = data.get("file_destination")

    user = create_user(
        username=username,
        password=password,
        doorbell_ip=doorbell_ip,
        cctv_ip=cctv_ip,
        file_destination=file_destination
    )

    if not user:
        return jsonify({"error": "User already exists"}), 409

    return jsonify({
        "message": "User created successfully",
        "username": user.username
    }), 201

# ==========================
# LOGIN (GET TOKEN)
# ==========================

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # 🔑 IMPORTANT: identity MUST be a STRING
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token
    })

# ==========================
# LOG VISITOR (PROTECTED)
# ==========================
@app.route("/api/visitors/log", methods=["POST"])
@jwt_required()
def api_log_visitor():
    """
    Log a visitor for the currently logged-in user.
    """
    user_id = int(get_jwt_identity())

    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    purpose = data.get("purpose")

    if not name:
        return jsonify({"error": "name is required"}), 400

    try:
        log = log_visitor(
            user_id=user_id,
            name=name,
            purpose=purpose
        )

        return jsonify({
            "status": "ok",
            "log": {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "name": log.name,
                "purpose": log.purpose
            }
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/visitor", methods=["POST"])
@jwt_required()
def add_visitor():
    user_id = int(get_jwt_identity())  # convert back to int

    data = request.get_json()
    name = data.get("name")
    purpose = data.get("purpose")

    if not name:
        return jsonify({"error": "visitor name required"}), 400

    log_visitor(
        user_id=user_id,
        name=name,
        purpose=purpose
    )

    return jsonify({"ok": True})

# ==========================
# GET ALL VISITORS (USER)
# ==========================

@app.route("/visitors", methods=["GET"])
@jwt_required()
def get_visitors():
    user_id = int(get_jwt_identity())

    logs = get_visitors_for_user(user_id)

    return jsonify([
        {
            "timestamp": l.timestamp.isoformat(),
            "name": l.name,
            "purpose": l.purpose
        }
        for l in logs
    ])




# ==========================
# GET TODAY'S VISITORS
# ==========================

@app.route("/visitors/today", methods=["GET"])
@jwt_required()
def get_today_visitors():
    user_id = int(get_jwt_identity())

    logs = get_today_visitors_for_user(user_id)

    return jsonify([
        {
            "timestamp": l.timestamp.isoformat(),
            "name": l.name,
            "purpose": l.purpose
        }
        for l in logs
    ])


from database.db import SessionLocal
from database.models import VisitorLog

@app.route("/api/visitors/clear", methods=["POST"])
@jwt_required()
def clear_all_visitors_for_user():
    """
    Clear ALL visitor logs for the currently logged-in user.
    """
    user_id = int(get_jwt_identity())

    db = SessionLocal()
    try:
        deleted = (
            db.query(VisitorLog)
            .filter(VisitorLog.user_id == user_id)
            .delete()
        )
        db.commit()

        return jsonify({
            "status": "ok",
            "deleted": deleted
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

    finally:
        db.close()

from flask_jwt_extended import jwt_required, get_jwt_identity
import subprocess, time

SYSTEM_SCRIPT = os.path.join(os.path.dirname(__file__), "system_main.py")

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

@app.route("/api/system/arm", methods=["POST"])
@jwt_required()
def arm_system():
    global _system_proc, _system_mode

    user_id = int(get_jwt_identity())   # 🔥 extract user from JWT

    data = request.get_json(force=True, silent=True) or {}
    armed = bool(data.get("armed"))
    mode = data.get("mode")

    if isinstance(mode, str):
        mode = mode.strip().lower()
    else:
        mode = None

    # ARM SYSTEM
    if armed:
        if _system_proc is not None and _system_proc.poll() is None:
            if mode == _system_mode:
                return jsonify({"status": "already_running", "mode": _system_mode}), 200
            _stop_system()

        py = subprocess.sys.executable
        args = [
            py,
            SYSTEM_SCRIPT,
            "--user-id", str(user_id)   # ✅ PASS USER ID
        ]

        if mode:
            args += ["--mode", mode]

        _system_proc = subprocess.Popen(args)
        _system_mode = mode

        time.sleep(0.2)
        if _system_proc.poll() is not None:
            return jsonify({"status": "error", "error": "process crashed"}), 500

        return jsonify({"status": "started", "mode": _system_mode}), 200

    # DISARM SYSTEM
    else:
        _stop_system()
        return jsonify({"status": "stopped"}), 200


@app.route("/api/assistant", methods=["POST"])
@jwt_required()
def assistant():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please enter a message."}), 400

    # 1️⃣ Fetch visitor logs
    logs = get_visitors_for_user(user_id)

    formatted_logs = "\n".join([
        f"- {l.name} | {l.timestamp} | purpose: {l.purpose}"
        for l in logs
    ]) or "No visitor logs available."

    # 2️⃣ Build prompt
    prompt = f"""
You are SecureHome Assistant.
The date today is {time.strftime("%Y-%m-%d %H:%M:%S")}.
Visitor logs:
{formatted_logs}

Rules:
- Answer ONLY using the visitor logs when relevant
- Be concise and security-focused
- If logs are insufficient, say so clearly

User question:
{user_message}
"""

    # 3️⃣ Call Gemini
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return jsonify({
        "reply": response.text
    })



@app.route("/api/communication/start", methods=["POST"])
@jwt_required()
def start_communication():
    ok, status = _start_communication()

    if not ok:
        return jsonify({
            "status": status
        }), 409

    return jsonify({
        "status": "running",
        "audio": "two.py",
        "video": "video.py"
    }), 200


@app.route("/api/communication/stop", methods=["POST"])
@jwt_required()
def stop_communication():
    _stop_communication()
    return jsonify({
        "status": "stopped"
    }), 200

# ==========================
# RUN SERVER
# ==========================


@app.route("/api/visitors/log-with-image", methods=["POST"])
@jwt_required()
def api_log_visitor_with_image():
    user_id = int(get_jwt_identity())

    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    purpose = data.get("purpose")
    message_id = data.get("message_id")   # ✅ Telegram message id

    if not name:
        return jsonify({"error": "name is required"}), 400

    try:
        log = log_visitor(
            user_id=user_id,
            name=name,
            purpose=purpose,
            message_id=message_id
        )

        return jsonify({
            "status": "ok",
            "log": {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "name": log.name,
                "purpose": log.purpose,
                "message_id": log.message_id
            }
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/visitors-pic", methods=["GET"])
@jwt_required()
def get_visitors_with_pics():
    user_id = int(get_jwt_identity())
    logs = get_visitors_with_pics_for_user(user_id)
    return jsonify(logs)



@app.route("/api/visitors/<int:visitor_id>/flag", methods=["POST"])
@jwt_required()
def set_visitor_flag(visitor_id):
    user_id = int(get_jwt_identity())

    db = SessionLocal()
    try:
        log = (
            db.query(VisitorLog)
            .filter(
                VisitorLog.id == visitor_id,
                VisitorLog.user_id == user_id
            )
            .first()
        )

        if not log:
            return jsonify({"error": "Visitor log not found"}), 404

        log.flag = 1
        db.commit()

        return jsonify({
            "status": "ok",
            "visitor_id": visitor_id,
            "flag": log.flag
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/api/visitors/<int:visitor_id>/unflag", methods=["POST"])
@jwt_required()
def unset_visitor_flag(visitor_id):
    user_id = int(get_jwt_identity())

    db = SessionLocal()
    try:
        log = (
            db.query(VisitorLog)
            .filter(
                VisitorLog.id == visitor_id,
                VisitorLog.user_id == user_id
            )
            .first()
        )

        if not log:
            return jsonify({"error": "Visitor log not found"}), 404

        log.flag = 0
        db.commit()

        return jsonify({
            "status": "ok",
            "visitor_id": visitor_id,
            "flag": log.flag
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


if __name__ == "__main__":
    app.run(
    host="0.0.0.0",  
    port=5000,
    debug=True
)

