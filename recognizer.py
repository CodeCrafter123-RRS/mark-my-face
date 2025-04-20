import cv2
import face_recognition
import numpy as np
import os
import csv
from datetime import datetime
from utils.whatsapp import send_whatsapp

STUDENTS_FILE = 'students_info.csv'
ATTENDANCE_FILE = 'attendance.csv'
PHOTOS_PATH = 'static/photos/'

# Desired field order for the attendance CSV
FIELDNAMES = ['photo', 'name', 'roll', 'status', 'date', 'time']

def load_known_faces():
    encodings, names, rolls, phones, photos = [], [], [], [], []
    with open(STUDENTS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            photo_file = row['photo'].strip()
            photo_path = os.path.join(PHOTOS_PATH, photo_file)
            if not os.path.exists(photo_path):
                print(f"[SKIPPED] Missing photo: {photo_path}")
                continue
            image = face_recognition.load_image_file(photo_path)
            try:
                encoding = face_recognition.face_encodings(image)[0]
                encodings.append(encoding)
                names.append(row['name'].strip())
                rolls.append(row['roll'].strip())
                phones.append(row['phone'].strip())
                photos.append(photo_file)
            except Exception as e:
                print(f"[FAILED] Face encoding failed for {photo_file}: {e}")
    return encodings, names, rolls, phones, photos

def ensure_attendance_file():
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def start_face_recognition():
    ensure_attendance_file()
    encodings, names, rolls, phones, photos = load_known_faces()
    recorded = set()

    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(encodings, face_encoding)
            face_distances = face_recognition.face_distance(encodings, face_encoding)

            if len(face_distances) == 0:
                continue

            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = names[best_match_index]
                roll = rolls[best_match_index]
                phone = phones[best_match_index]
                photo = photos[best_match_index]

                if roll not in recorded:
                    recorded.add(roll)

                    now = datetime.now()
                    time_str = now.strftime("%H:%M:%S")
                    date_str = now.strftime("%Y-%m-%d")

                    # ✅ Append correct data in correct format
                    with open(ATTENDANCE_FILE, 'a', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                        writer.writerow({
                            'photo': photo,
                            'name': name,
                            'roll': roll,
                            'status': 'Present',
                            'date': date_str,
                            'time': time_str
                        })
                        print(f"[LOGGED] {photo}, {name}, {roll}, Present, {date_str}, {time_str}")

                    # ✅ Send WhatsApp notification
                    send_whatsapp(phone, f"Hi {name}, your attendance was marked on {date_str} at {time_str}.")

                # ✅ Show bounding box
                top, right, bottom, left = [v * 4 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow('Face Attendance - Press Q to Quit', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
