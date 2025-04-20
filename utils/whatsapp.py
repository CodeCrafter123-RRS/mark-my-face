import pandas as pd
from datetime import datetime
from pywhatkit import sendwhatmsg_instantly

def send_whatsapp_notification(name):
    try:
        # Normalize name
        name = name.strip().lower()

        # Load student info
        df = pd.read_csv('students_info.csv')
        df['Name'] = df['Name'].str.strip().str.lower()

        # Find the student
        student = df[df['Name'] == name]

        if not student.empty:
            phone = str(student.iloc[0]['Phone']).strip().replace(" ", "").replace("+91", "")
            now = datetime.now()
            message = f"Hi {name.title()}, your attendance has been marked at {now.strftime('%H:%M:%S on %d-%m-%Y')}."

            # Send WhatsApp message
            sendwhatmsg_instantly(f"+91{phone}", message, wait_time=10, tab_close=True)

            print(f"✅ WhatsApp message sent to {name} at {phone}")

        else:
            print(f"❌ No phone number found for {name}")

    except Exception as e:
        print(f"[WhatsApp Error] {e}")
