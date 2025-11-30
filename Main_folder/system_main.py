import os
import sys
import time
import requests
from datetime import datetime
import pyttsx3
import argparse
import signal
import threading
import time
import subprocess
from database.utils import log_visitor

from database.utils import clear_all_visitors

from database.utils import print_all_visitors

# system_main.py (or at top of your existing file)

    
# ensure tables exist at process start (call once)
# safe to call; remove or set drop_first=True only in dev if neede
# import your detection libs here

_stop_event = threading.Event()

def _handle_term(signum, frame):
    print("[system_main] signal received:", signum)
    _stop_event.set()

signal.signal(signal.SIGTERM, _handle_term)
signal.signal(signal.SIGINT, _handle_term)

def speak(text):
    engine = pyttsx3.init()
    
    # make it slower and smoother
    engine.setProperty("rate", 150)      # slower pace
    engine.setProperty("volume", 0.9)    # softer volume
    
    # choose a different voice (if available)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id) 
    
    print(text)
    engine.say(text)
    engine.runAndWait()

# add Face folder to import path (so we can "from face_module import ...")
THIS_DIR = os.path.dirname(__file__)
FACE_DIR = os.path.abspath(os.path.join(THIS_DIR, "..", "Face"))
if FACE_DIR not in sys.path:
    sys.path.insert(0, FACE_DIR)

from face_module import monitor_door_and_capture, load_known_faces



# ==== TELEGRAM CONFIG ========
TELEGRAM_BOT_TOKEN = "XXXXXXX:YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
TELEGRAM_CHAT_ID = "XXX"
# ==============================

# Where the encodings pickle lives
ENCODINGS_PKL = os.path.join(FACE_DIR, "known_faces_encodings.pkl")
ALERT_FRAME_PATH = os.path.join(FACE_DIR, "alert_frame.jpg")

# Telegram helpers
def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[system_main] Telegram sendMessage failed: {e}")

def send_telegram_photo(photo_path: str, caption: str = ""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
            r = requests.post(url, files=files, data=data, timeout=20)
            r.raise_for_status()
    except Exception as e:
        print(f"[system_main] Telegram sendPhoto failed: {e}")

def human_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main_loop():
    # Load known faces (supports the tuple or dict formats)
    known_encs, known_names = load_known_faces(ENCODINGS_PKL)
    print(f"[system_main] Loaded {len(known_names)} known faces.")

    print("[system_main] Starting monitor loop. Press Ctrl+C to stop.")
    try:
        while True:
            # Call the face monitor (blocks until confirmed face or timeout)
            result = monitor_door_and_capture(
                video_source=0,
                known_face_encodings=known_encs,
                known_face_names=known_names,
                alert_frame_path=ALERT_FRAME_PATH,
                required_consecutive=5,   # raise this if you want stricter confirmation
                tolerance=0.45,           # lower -> stricter matching
                resize_scale=0.25,
                timeout=30.0
            )

            if result is None:
                # Defensive: treat as timeout
                print(f"[{human_time()}] No result returned from face_module.")
                send_telegram_message("🚪 Someone at the door, but no face could be confirmed.")
                time.sleep(1)
                continue

            if result["status"] == "confirmed":
                label = result["label"] or "UNKNOWN"
                path = result["frame_path"]

                if label != "UNKNOWN":
                    print(f"[{human_time()}] Visitor confirmed: {label}")
                    send_telegram_message(f"🚪 Visitor detected: {label}")
                else:
                    print(f"[{human_time()}] Unknown visitor detected.")
                    send_telegram_message("🚪 Unknown visitor at the door!")

                # attach photo if saved
                if path and os.path.exists(path):
                    send_telegram_photo(path, caption=f"Visitor: {label}")
                else:
                    print("[system_main] No alert image found to attach.")
            else:
                # timeout case
                print(f"[{human_time()}] monitor timed out without detecting a persistent face.")
                # Optionally notify: you can comment next line if you don't want timeout messages
                send_telegram_message("🚪 Someone came to the door, but no face could be confirmed.")

            # small delay to avoid tight-loop repeat spamming
            time.sleep(0.5)
            return label

    except KeyboardInterrupt:
        print("\n[system_main] Stopped by user. Exiting.")


def convoifknown(label,label_prev):
    speak("Hi "+label+" , Welcome home!")
    time.sleep(0.25)
    speak(label_prev+ " entered home recently")
    return "An unknown person" if label == "UNKNOWN" else label


def run_stt_tts():
    """Try to import run_conversation from STT_TTS and call it directly.
    If that fails, fall back to launching the STT_TTS.py script as a subprocess.

    Returns:
        tuple: (name, visitor_text) if direct call succeeded,
               (None, None) if fallback/subprocess used or there was an error.
    """
    stt_script = os.path.join(THIS_DIR, "STT_TTS.py")
    try:
        # Attempt direct import & call for cleaner integration
        print("[system_main] Attempting to call STT_TTS.run_conversation() directly...")
        # If STT_TTS.py is next to this file, this import should work.
        from STT_TTS import run_conversation  # type: ignore
        name, visitor_text = run_conversation()
        print(f"[system_main] STT_TTS returned name={name}, text={visitor_text}")
        return name, visitor_text
    except Exception as e:
        # If anything fails (import error, runtime error inside STT_TTS, missing deps),
        # fall back to launching the script as a subprocess — preserving previous behavior.
        print(f"[system_main] Direct call to STT_TTS failed: {e}. Falling back to subprocess.")
        try:
            subprocess.run([sys.executable, stt_script], check=False)
        except Exception as e2:
            print(f"[system_main] Failed to run STT_TTS via subprocess: {e2}")
        return None, None

def childsafety():
    speak("Child safety mode activated.")

def nightmode():
    speak("Night mode activated.")

#===========_-_-_-_-_-_-_-_-_-MAIN EXCECUTION STARTS HERE_-_-_-_-_-_-_-_-_-=============#

def surveillance_loop(mode):
    print(f"[system_main] starting in mode='{mode}'")
    label_prev = "Nobody"
    purpose_main = "TEMPORARY PURPOSE"
    name_main = "Name"
    try:
        while not _stop_event.is_set():
            # call your detection function that returns label or "UNKNOWN"
            label = main_loop()   # keep your existing function
            if mode == "normal" :
                if label != "UNKNOWN" : 
                    log_visitor(name=label, purpose="Home owner")
                    label_prev = convoifknown(label, label_prev)
                else :
                    # Here we still call run_stt_tts(); it now returns (name, visitor_text)
                    # but existing code flow is preserved. We simply call it and ignore return
                    # if you want to use the returned values later, update logic accordingly.
                    _ret_name, _ret_text = run_stt_tts()
                    log_visitor(name="Unknown: "+_ret_name, purpose=_ret_text)
                    label_prev = "An Unknown person"
            elif mode == "child" :
                if label != "UNKNOWN" : 
                    log_visitor(name=label, purpose="Home owner")
                    label_prev = convoifknown(label, label_prev)
                else :
                    ret_name, _ret_text = run_stt_tts()
                    log_visitor(name="Unknown: "+ret_name, purpose=_ret_text)
                    label_prev = "An Unknown person"
            elif mode == "night" :  
                if label != "UNKNOWN" :
                    log_visitor(name=label, purpose="Home owner")
                    label_prev = convoifknown(label, label_prev)
                else :
                    ret_name, _ret_text = run_stt_tts()
                    log_visitor(name="Unknown: "+ret_name, purpose=_ret_text)
                    label_prev = "An Unknown person"
            for _ in range(5):
                if _stop_event.is_set():
                    break
                time.sleep(0.1)
    finally:
        # cleanup cameras / windows / models here
        print("[system_main] cleaning up")
        # release camera example: cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="normal")
    args = parser.parse_args()
    surveillance_loop(args.mode.lower())

#===========_-_-_-_-_-_-_-_-_-MAIN EXCECUTION ENDS HERE_-_-_-_-_-_-_-_-_-=============#
