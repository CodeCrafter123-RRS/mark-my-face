from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils.face_utils import save_face_encoding
from werkzeug.utils import secure_filename
import cv2
import face_recognition
import numpy as np
import pickle
import pandas as pd
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODINGS_FILE = os.path.join(BASE_DIR, 'models/face_encodings.pkl')
ATTENDANCE_FILE = os.path.join(BASE_DIR, 'attendance.csv')
STUDENTS_FILE = os.path.join(BASE_DIR, 'students_info.csv')
PHOTOS_DIR = os.path.join(BASE_DIR, 'static/photos')
UPLOAD_FOLDER = os.path.join(BASE_DIR,'static/photos')

# Ensure directories exist
os.makedirs(os.path.dirname(ENCODINGS_FILE), exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dummy WhatsApp notification function
def send_whatsapp_notification(name):
    print(f"[NOTIFY] WhatsApp notification sent to {name}")

# User verification
def verify_user(email, password):
    file_path = 'users.csv'
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['email', 'password'])
            writer.writeheader()
            writer.writerow({'email': 'admin@example.com', 'password': 'admin123'})
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'] == email and row['password'] == password:
                return True
    return False

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        phone = request.form['phone']
        photo = request.files['photo']

        if not (name and roll and phone and photo):
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        filename = secure_filename(name.lower().replace(" ", "_") + os.path.splitext(photo.filename)[1])
        photo_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(photo_path)

        # Save to students_info.csv
        csv_file = 'students_info.csv'
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Name', 'Roll', 'Phone', 'Photo'])
            writer.writerow([name, roll, phone, filename])

        flash("Student registered successfully!", "success")
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/start')
def start_attendance():
    import cv2
    import face_recognition
    import pickle
    import numpy as np
    from utils.database import mark_attendance  # make sure this is correct

    # ✅ Load known encodings
    try:
        with open('models/face_encodings.pkl', 'rb') as f:
            known_encodings_data = pickle.load(f)
        known_encodings = known_encodings_data['encodings']
        known_names = known_encodings_data['names']
    except Exception as e:
        return f"Error loading face encodings: {e}", 500

    # ✅ Start webcam
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        return "Failed to access the camera. Check the webcam or IP camera link.", 500

    while True:
        success, frame = cap.read()
        if not success:
            print("[ERROR] Failed to read from camera")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for encoding, face_loc in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, encoding)
            print(f"[DEBUG] Face distances: {face_distances}")

            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]
                print(f"[DEBUG] Match found: {name}")
                mark_attendance(name)

                # Draw rectangle
                y1, x2, y2, x1 = [v * 4 for v in face_loc]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, name, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imshow('Attendance System - Press q to Quit', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return redirect(url_for('index'))

@app.route('/attendance')
def attendance():
    attendance_records = []
    try:
        with open('attendance.csv', 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print(row)  # 🪵 DEBUG
                if 'name' in row:
                    photo_filename = f"{row['name'].lower().replace(' ', '_')}.jpg"
                    attendance_records.append({
                        'photo': photo_filename,
                        'name': row.get('name', 'Unknown'),
                        'roll': row.get('roll', 'N/A'),
                        'status': row.get('status', 'N/A'),
                        'time': row.get('time', 'N/A'),
                        'date': row.get('date', 'N/A')
                    })
    except Exception as e:
        print(f"Error reading attendance.csv: {e}")

    print(f"Total records loaded: {len(attendance_records)}")  # 🪵 DEBUG
    return render_template('attendance.html', attendance=attendance_records)

@app.route('/students')
def view_students():
    students = []
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                students.append({
                    'photo': row['photo'],
                    'name': row['name'],
                    'roll': row['roll'],
                    'phone': row['phone']
                })
    return render_template('students.html', students=students)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if add_user(name, email, password):
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User already exists!', 'danger')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if verify_user(email, password):
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/notifications')
def notifications():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('notification_history.html')

if __name__ == '__main__':
    print("✅ Flask app is starting at http://127.0.0.1:5000")
    app.run(debug=True)
