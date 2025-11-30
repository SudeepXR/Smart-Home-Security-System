import os
import time
import pickle
from collections import deque
from datetime import datetime

import numpy as np
import cv2
import face_recognition
import pyttsx3


def speak(text):
    engine = pyttsx3.init()
    
    # make it slower and smoother
    engine.setProperty("rate", 150)      # slower pace
    engine.setProperty("volume", 0.9)    # softer volume
    
    # choose a different voice (if available)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id)  # try female/male
    
    print(text)
    engine.say(text)
    engine.runAndWait()

def load_known_faces(pkl_path):
    if not os.path.exists(pkl_path):
        print(f"[face_module] No encodings file at {pkl_path} -> using empty known list")
        return [], []
    try:
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)
    except Exception as e:
        print(f"[face_module] Failed to load pickle {pkl_path}: {e}")
        return [], []
    if isinstance(data, tuple) and len(data) >= 2:
        return data[0], data[1]
    if isinstance(data, dict):
        if "encodings" in data and "names" in data:
            return data["encodings"], data["names"]
        if "encs" in data and "names" in data:
            return data["encs"], data["names"]
    try:
        return data[0], data[1]
    except Exception:
        print("[face_module] Unknown pickle format for known faces. Returning empty lists.")
        return [], []


def monitor_door_and_capture(
    video_source=0,
    known_face_encodings=None,
    known_face_names=None,
    alert_frame_path=None,
    required_consecutive=5,
    tolerance=0.45,
    resize_scale=0.25,
    timeout=30.0,
    margin_ratio=0.25,
    detection_model="hog",
):
    if known_face_encodings is None:
        known_face_encodings = []
    if known_face_names is None:
        known_face_names = []

    if alert_frame_path is None:
        alert_frame_path = os.path.join(os.path.dirname(__file__), "alert_frame.jpg")

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        raise RuntimeError(f"[face_module] Cannot open video source {video_source}")

    start_time = time.time()
    labels_deque = deque(maxlen=required_consecutive)
    distances_deque = deque(maxlen=required_consecutive)

    face_prompt_given = False  # flag so we don’t repeat speech constantly

    try:
        while True:

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=resize_scale, fy=resize_scale)

            face_locations = face_recognition.face_locations(small_frame, model=detection_model)

            if not face_locations:
                labels_deque.clear()
                distances_deque.clear()
                face_prompt_given = False  # reset, so it speaks again next time
                cv2.imshow("Door Camera", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            # >>> NEW: speak when any face is seen
            '''if not face_prompt_given:
                speak("Please stand still and in front of the camera.")
                face_prompt_given = True'''

            areas = [(b - t) * (r - l) for (t, r, b, l) in face_locations]
            best_idx = int(np.argmax(areas))
            best_loc = face_locations[best_idx]

            encs = face_recognition.face_encodings(small_frame, [best_loc])
            if not encs:
                labels_deque.clear()
                distances_deque.clear()
                cv2.imshow("Door Camera", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue
            encoding = encs[0]

            label = "UNKNOWN"
            best_distance = None
            if len(known_face_encodings) > 0:
                dists = face_recognition.face_distance(known_face_encodings, encoding)
                best_idx2 = int(np.argmin(dists))
                best_distance = float(dists[best_idx2])
                if best_distance <= tolerance:
                    label = known_face_names[best_idx2]

            labels_deque.append(label)
            distances_deque.append(best_distance if best_distance is not None else float("inf"))

            # Draw bounding box & label on the frame
            t, r, b, l = best_loc
            scale = 1.0 / resize_scale
            t_o = int(t * scale)
            r_o = int(r * scale)
            b_o = int(b * scale)
            l_o = int(l * scale)

            color = (0, 255, 0) if label != "UNKNOWN" else (0, 0, 255)
            cv2.rectangle(frame, (l_o, t_o), (r_o, b_o), color, 2)
            cv2.putText(
                frame,
                label,
                (l_o, t_o - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
            )

            cv2.imshow("Door Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if (
                len(labels_deque) == required_consecutive
                and all(x == labels_deque[0] for x in labels_deque)
            ):
                confirmed_label = labels_deque[0]
                t, r, b, l = best_loc
                scale = 1.0 / resize_scale
                t_o = int(max(0, round(t * scale)))
                r_o = int(min(frame.shape[1], round(r * scale)))
                b_o = int(min(frame.shape[0], round(b * scale)))
                l_o = int(max(0, round(l * scale)))

                width_o = r_o - l_o
                margin = int(width_o * margin_ratio)
                t_c = max(0, t_o - margin)
                l_c = max(0, l_o - margin)
                b_c = min(frame.shape[0], b_o + margin)
                r_c = min(frame.shape[1], r_o + margin)

                face_crop = frame[t_c:b_c, l_c:r_c]
                folder = os.path.dirname(alert_frame_path)
                if folder and not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)
                cv2.imwrite(alert_frame_path, face_crop)

                avg_distance = None
                valid_dists = [
                    d for d in distances_deque if d is not None and not np.isinf(d)
                ]
                if valid_dists:
                    avg_distance = float(np.mean(valid_dists))

                cv2.destroyAllWindows()
                return {
                    "status": "confirmed",
                    "label": confirmed_label,
                    "distance": avg_distance,
                    "frame_path": os.path.abspath(alert_frame_path),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }

    finally:
        cap.release()
        cv2.destroyAllWindows()
