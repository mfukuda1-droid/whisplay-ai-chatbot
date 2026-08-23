import face_recognition
import pickle
import sys
import os
import json
import tempfile
import fcntl

ENCODINGS_PATH = os.environ.get("FACE_ENCODINGS_PATH", "data/known_faces/encodings.pkl")


def register(name, image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if not encodings:
        return {"ok": False, "reason": "no_face_detected"}
    if len(encodings) != 1:
        return {
            "ok": False,
            "reason": "multiple_faces_detected",
            "face_count": len(encodings),
        }

    encodings_dir = os.path.dirname(ENCODINGS_PATH) or "."
    os.makedirs(encodings_dir, exist_ok=True)
    lock_path = ENCODINGS_PATH + ".lock"
    with open(lock_path, "a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        data = {}
        if os.path.exists(ENCODINGS_PATH):
            with open(ENCODINGS_PATH, "rb") as f:
                data = pickle.load(f)

        data.setdefault(name, [])
        data[name].append(encodings[0])

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=encodings_dir, delete=False
            ) as temp_file:
                temp_path = temp_file.name
                pickle.dump(data, temp_file)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, ENCODINGS_PATH)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    return {"ok": True, "name": name, "sample_count": len(data[name])}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使い方: python3 register_face.py <名前> <画像パス>")
        sys.exit(1)
    try:
        result = register(sys.argv[1], sys.argv[2])
        print(json.dumps(result, ensure_ascii=False))
        if not result["ok"]:
            sys.exit(2)
    except Exception as error:
        print(json.dumps({"ok": False, "reason": "registration_failed"}))
        print(f"顔登録に失敗しました: {error}", file=sys.stderr)
        sys.exit(1)
