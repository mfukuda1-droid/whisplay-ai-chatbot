import face_recognition
import pickle
import sys
import os

ENCODINGS_PATH = "data/known_faces/encodings.pkl"

def register(name, image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if not encodings:
        print(f"顔が検出できませんでした: {image_path}")
        return

    os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)
    data = {}
    if os.path.exists(ENCODINGS_PATH):
        with open(ENCODINGS_PATH, "rb") as f:
            data = pickle.load(f)

    data.setdefault(name, [])
    data[name].append(encodings[0])

    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(data, f)
    print(f"登録完了: {name}（{len(data[name])}枚目）")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使い方: python3 register_face.py <名前> <画像パス>")
        sys.exit(1)
    register(sys.argv[1], sys.argv[2])
