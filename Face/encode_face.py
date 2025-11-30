import os
import pickle
import face_recognition

KNOWN_FACES_DIR = "Pics"
ENCODINGS_FILE = "known_faces_encodings.pkl"

known_face_encodings = []
known_face_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            print(f"No faces found in {filename}, skipping.")
            continue
        known_face_encodings.append(encodings[0])
        name = filename.split("_")[0]
        known_face_names.append(name)

with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump((known_face_encodings, known_face_names), f)

print(f"Saved encodings for {len(known_face_names)} faces.")
