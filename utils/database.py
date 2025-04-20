import csv
import os
import hashlib
from datetime import datetime
from utils.whatsapp import send_whatsapp_notification

STUDENTS_FILE = 'students_info.csv'
ATTENDANCE_FILE = 'attendance.csv'
USERS_FILE = 'users.csv'

# Hash passwords for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Add new user (sign up)
def add_user(name, email, password):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'email', 'password'])

    with open(USERS_FILE, 'r') as f:
        for row in csv.DictReader(f):
            if row['email'] == email:
                return False

    with open(USERS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, email, hash_password(password)])
    return True

# Login check
def verify_user(email, password):
    if not os.path.exists(USERS_FILE):
        return False
    hashed = hash_password(password)
    with open(USERS_FILE, 'r') as f:
        for row in csv.DictReader(f):
            if row['email'] == email and row['password'] == hashed:
                return True
    return False

# Save new student
def save_student_info(name, roll, phone, photo_filename):
    if not os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'roll', 'phone', 'photo'])

    with open(STUDENTS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, roll, phone, photo_filename])

# Get all students
def get_all_students():
    students = []
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'r') as f:
            for row in csv.DictReader(f):
                students.append(row)
    return students

def mark_attendance(name):
    today = datetime.now().strftime('%Y-%m-%d')
    already_marked = False

    # Ensure the attendance file exists with proper headers
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['photo', 'name', 'roll', 'status', 'date', 'time'])

    # Check if already marked
    with open(ATTENDANCE_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['name'] == name and row['date'] == today:
                already_marked = True
                break

    if not already_marked:
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        # Get photo filename and roll number from students_info.csv
        photo_filename = ""
        roll_no = ""
        with open(STUDENTS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name'].strip().lower() == name.strip().lower():
                    photo_filename = row['photo']
                    roll_no = row['roll']
                    break

        # Final write
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([photo_filename, name, roll_no, 'Present', date_str, time_str])

        send_whatsapp_notification(name)
        print(f"✅ Marked present: {name}")

# Get attendance stats
def get_attendance_stats():
    stats = {}
    total_days = set()
    records = {}

    if not os.path.exists(ATTENDANCE_FILE):
        return {'labels': [], 'values': []}

    with open(ATTENDANCE_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            date = row['date']
            total_days.add(date)
            if name not in records:
                records[name] = set()
            records[name].add(date)

    total_days_count = len(total_days)
    labels = []
    values = []

    for student, dates in records.items():
        labels.append(student)
        percentage = (len(dates) / total_days_count) * 100 if total_days_count else 0
        values.append(round(percentage, 2))

    return {'labels': labels, 'values': values}
