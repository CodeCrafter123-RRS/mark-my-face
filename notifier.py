import pywhatkit

def send_whatsapp(phone, message="Your attendance has been marked."):
    try:
        # Ensure phone number starts with country code
        if not phone.startswith('+'):
            phone = '+91' + phone.strip()  # Modify this based on your location

        print(f"📲 Sending WhatsApp message to {phone}...")
        pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=10, tab_close=True)

    except Exception as e:
        print("❌ WhatsApp Error:", e)
