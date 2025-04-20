import os
import cv2
import face_recognition
import pickle

dataset_dir = 'static/photos'  # folder where student images are saved
known_encodings = []
known_names = []

for filename in os.listdir(dataset_dir):
    if filename.endswith(('.jpg', '.png', '.jpeg')):
        path = os.path.join(dataset_dir, filename)
        img = cv2.imread(path)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        if encodings:
            known_encodings.append(encodings[0])
            name = os.path.splitext(filename)[0]
            known_names.append(name)
        else:
            print(f"[WARNING] No face found in {filename}")

# Save to pickle
data = {"encodings": known_encodings, "names": known_names}
with open("models/face_encodings.pkl", "wb") as f:
    pickle.dump(data, f)

print("✅ Face encodings generated and saved to 'models/face_encodings.pkl'")
