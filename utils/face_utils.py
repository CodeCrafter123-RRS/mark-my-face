import face_recognition
import os
import pickle

def save_face_encoding(image_path, student_name):
    try:
        print(f"📸 Encoding face from: {image_path}")

        if not os.path.exists(image_path):
            print("❌ Image file not found!")
            return False

        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)

        if not face_locations:
            print("❌ No face found in the image.")
            return False

        encoding = face_recognition.face_encodings(image, face_locations)[0]

        # Ensure models folder exists
        os.makedirs("models", exist_ok=True)

        encodings_path = os.path.join("models", "face_encodings.pkl")

        # Load or initialize encoding dictionary
        if os.path.exists(encodings_path):
            with open(encodings_path, "rb") as f:
                known_encodings = pickle.load(f)
        else:
            known_encodings = {}

        known_encodings[student_name] = encoding

        # Save updated encodings
        with open(encodings_path, "wb") as f:
            pickle.dump(known_encodings, f)

        print("✅ Encoding saved to face_encodings.pkl")
        return True

    except Exception as e:
        print(f"🔥 ERROR while encoding: {e}")
        return False
