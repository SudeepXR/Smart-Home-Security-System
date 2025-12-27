import os
import sys
import time
import requests
import argparse
import signal
import threading
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import pyttsx3

# Local Imports
from database.utils import log_visitor
# Ensure Face folder is in path for face_module
THIS_DIR = os.path.dirname(__file__)
FACE_DIR = os.path.abspath(os.path.join(THIS_DIR, "..", "Face"))
if FACE_DIR not in sys.path:
    sys.path.insert(0, FACE_DIR)

from face_module import monitor_door_and_capture, load_known_faces

# Load Environment Variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ENCODINGS_PKL = os.path.join(FACE_DIR, "known_faces_encodings.pkl")
ALERT_FRAME_PATH = os.path.join(FACE_DIR, "alert_frame.jpg")

# Control Events
_stop_event = threading.Event()

def _handle_term(signum, frame):
    print(f"\n[system_main] Signal {signum} received. Shutting down...")
    _stop_event.set()

signal.signal(signal.SIGTERM, _handle_term)
signal.signal(signal.SIGINT, _handle_term)

# --- TTS Engine Setup ---
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.setProperty("volume", 0.9)
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)
        
        print(f"[TTS]: {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error]: {e}")

# --- Telegram Helpers ---
def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"[Telegram] Error: {e}")

def send_telegram_photo(photo_path: str, caption: str = ""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not os.path.exists(photo_path): return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as f:
            requests.post(url, files={"photo": f}, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, timeout=20)
    except Exception as e:
        print(f"[Telegram] Photo Error: {e}")

# --- STT Logic ---
def run_stt_tts():
    stt_script = os.path.join(THIS_DIR, "STT_TTS.py")
    try:
        from STT_TTS import run_conversation
        return run_conversation()
    except Exception:
        try:
            subprocess.run([sys.executable, stt_script], check=False)
        except Exception as e:
            print(f"[STT Error]: {e}")
        return "Unknown", "No message"

# --- Main Logic ---
def convo_logic(label, label_prev):
    if label != "UNKNOWN":
        speak(f"Hi {label}, Welcome home!")
        time.sleep(0.25)
        speak(f"{label_prev} entered home recently.")
        return label
    else:
        speak("I don't recognize you. Please state your name and purpose.")
        return "An unknown person"

def surveillance_loop(user_id, mode):
    print(f"[system_main] Running for User: {user_id} | Mode: {mode}")
    label_prev = "Nobody"
    
    known_encs, known_names = load_known_faces(ENCODINGS_PKL)
    
    try:
        while not _stop_event.is_set():
            result = monitor_door_and_capture(
                video_source=0,
                known_face_encodings=known_encs,
                known_face_names=known_names,
                alert_frame_path=ALERT_FRAME_PATH,
                required_consecutive=5,
                tolerance=0.45,
                timeout=30.0
            )

            if result and result["status"] == "confirmed":
                label = result["label"] or "UNKNOWN"
                
                # Notification
                msg = f"🚪 Visitor: {label}" if label != "UNKNOWN" else "⚠️ Unknown visitor detected!"
                send_telegram_message(msg)
                if os.path.exists(result["frame_path"]):
                    send_telegram_photo(result["frame_path"], caption=f"Detected: {label}")

                # Logic branching based on identity
                if label != "UNKNOWN":
                    log_visitor(user_id=user_id, name=label, purpose="Home owner")
                    label_prev = convo_logic(label, label_prev)
                else:
                    # Specific behaviors for modes can be added here
                    if mode == "night":
                        speak("Night mode is active. Security has been alerted.")
                    
                    name_input, purpose_input = run_stt_tts()
                    log_visitor(user_id=user_id, name=f"Unknown: {name_input}", purpose=purpose_input)
                    label_prev = "An unknown person"

            time.sleep(1)
    finally:
        print("[system_main] Cleaning up and exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user-id",
        type=int,
        default=0,          # ✅ default user (local/manual run)
        help="User ID for database logging"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="normal"
    )

    args = parser.parse_args()

    print(f"[system_main] Starting | user_id={args.user_id} | mode={args.mode}")

    surveillance_loop(args.user_id, args.mode.lower())