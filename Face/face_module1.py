import os
import time
import pickle
from collections import deque
from datetime import datetime

import numpy as np
import cv2
import face_recognition

# -------------------------
# Load known faces
# -------------------------
def load_known_faces(pkl_path):
    if not os.path.exists(pkl_path):
        print(f"[face_module] No encodings file at {pkl_path}")
        return [], []

    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    if isinstance(data, tuple):
        return data[0], data[1]
    if isinstance(data, dict):
        return data.get("encodings", []), data.get("names", [])
    return [], []

# -------------------------
# Eye Aspect Ratio (EAR)
# -------------------------
def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    print((A + B) / (2.0 * C))
    return (A + B) / (2.0 * C)

# -------------------------
# Main monitor (ORIGINAL FLOW + BLINK GUARD)
# -------------------------
def monitor_door_and_capture(
    video_source=1,
    known_face_encodings=None,
    known_face_names=None,
    alert_frame_path=None,
    required_consecutive=5,
    tolerance=0.45,
    resize_scale=0.25,
    timeout=180.0,
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
        raise RuntimeError("Cannot open camera")

    start_time = time.time()
    labels_deque = deque(maxlen=required_consecutive)
    distances_deque = deque(maxlen=required_consecutive)

    # -------------------------
    # Blink state machine (LOW FPS SAFE)
    # -------------------------
    EAR_THRESHOLD = 0.21
    eye_state = "OPEN"
    blink_seen = False

    try:
        while True:
            if time.time() - start_time > timeout:
                return None

            ret, frame = cap.read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small_frame = cv2.resize(
                rgb_frame, (0, 0), fx=resize_scale, fy=resize_scale
            )

            face_locations = face_recognition.face_locations(
                small_frame, model=detection_model
            )

            # -------- RESET WHEN NO FACE --------
            if not face_locations:
                labels_deque.clear()
                distances_deque.clear()
                eye_state = "OPEN"
                blink_seen = False
                cv2.imshow("Door Camera", frame)
                cv2.waitKey(1)
                continue

            # -------- BLINK CHECK (STATE TRANSITION) --------
            landmarks = face_recognition.face_landmarks(
                small_frame, face_locations
            )
            for lm in landmarks:
                if "left_eye" in lm and "right_eye" in lm:
                    left = np.array(lm["left_eye"])
                    right = np.array(lm["right_eye"])
                    ear = (eye_aspect_ratio(left) + eye_aspect_ratio(right)) / 2.0

                    if ear < EAR_THRESHOLD and eye_state == "OPEN":
                        eye_state = "CLOSED"

                    elif ear >= EAR_THRESHOLD and eye_state == "CLOSED":
                        blink_seen = True
                        eye_state = "OPEN"

            # -------- ORIGINAL: choose largest face --------
            areas = [(b - t) * (r - l) for (t, r, b, l) in face_locations]
            best_idx = int(np.argmax(areas))
            best_loc = face_locations[best_idx]

            encs = face_recognition.face_encodings(
                small_frame, [best_loc]
            )
            if not encs:
                continue

            encoding = encs[0]
            label = "UNKNOWN"
            best_distance = None

            if known_face_encodings:
                dists = face_recognition.face_distance(
                    known_face_encodings, encoding
                )
                idx = int(np.argmin(dists))
                best_distance = float(dists[idx])
                if best_distance <= tolerance:
                    label = known_face_names[idx]

            labels_deque.append(label)
            distances_deque.append(
                best_distance if best_distance is not None else float("inf")
            )

            # -------- DRAW BOX & LABEL (UNCHANGED) --------
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
            cv2.waitKey(1)

            # -------- FINAL CONFIRMATION (BLINK GUARDED) --------
            if (
                len(labels_deque) == required_consecutive
                and all(x == labels_deque[0] for x in labels_deque)
            ):
                if not blink_seen:
                    continue  # wait for blink

                # ORIGINAL confirmation behavior
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
                os.makedirs(os.path.dirname(alert_frame_path), exist_ok=True)
                cv2.imwrite(alert_frame_path, face_crop)

                valid = [d for d in distances_deque if not np.isinf(d)]
                avg_distance = float(np.mean(valid)) if valid else None

                return {
                    "status": "confirmed",
                    "label": label,
                    "distance": avg_distance,
                    "frame_path": os.path.abspath(alert_frame_path),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }

    finally:
        cap.release()
        cv2.destroyAllWindows()