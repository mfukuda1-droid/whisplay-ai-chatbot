import face_recognition
import pickle
import sys
import json
import os

ENCODINGS_PATH = os.environ.get("FACE_ENCODINGS_PATH", "data/known_faces/encodings.pkl")
TOLERANCE = 0.5  # 小さいほど厳しく判定（似た家族間で誤認識するなら下げる）

def recognize(image_path, tolerance=TOLERANCE):
    if not os.path.exists(ENCODINGS_PATH):
        print(json.dumps({"name": None, "reason": "no_encodings_file"}))
        return

    with open(ENCODINGS_PATH, "rb") as f:
        data = pickle.load(f)

    image = face_recognition.load_image_file(image_path)
    unknown_encodings = face_recognition.face_encodings(image)

    if not unknown_encodings:
        print(json.dumps({"name": None, "reason": "no_face_detected"}))
        return

    unknown = unknown_encodings[0]
    best_name, best_dist = None, 1.0
    for name, known_list in data.items():
        distances = face_recognition.face_distance(known_list, unknown)
        min_dist = min(distances)
        if min_dist < best_dist:
            best_dist, best_name = min_dist, name

    if best_name is not None and best_dist <= tolerance:
        print(json.dumps({"name": best_name, "distance": round(float(best_dist), 3)}))
    else:
        print(json.dumps({"name": None, "distance": round(float(best_dist), 3) if best_name else None}))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"name": None, "reason": "usage: recognize_face.py <image_path>"}))
        sys.exit(1)
    recognize(sys.argv[1])
