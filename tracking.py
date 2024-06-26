import pyrebase
import serial
import pynmea2
import atexit

firebaseConfig = {
    "apiKey": "AIzaSyC8zYpL1c5oGUQ1IZK13tSsad7J53tNXCg",
    "authDomain": "blind-gps-tracker.firebaseapp.com",
    "databaseURL": "https://blind-gps-tracker-default-rtdb.firebaseio.com",
    "projectId": "blind-gps-tracker",
    "storageBucket": "blind-gps-tracker.appspot.com",
    "messagingSenderId": "547895832369",
    "appId": "1:547895832369:web:2f500aed48271eb8f78a10"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

db.update({"trackingConfirmed": False})
db.update({"trackingRequested": False})

port = "/dev/ttyACM0"
ser = serial.Serial(port, baudrate=9600, timeout=0.5)
dataout = pynmea2.NMEAStreamReader()

last_valid_lat = None
last_valid_lng = None

def cleanup():
    db.update({"trackingRequested": False})
    db.update({"trackingConfirmed": False})

atexit.register(cleanup)

try:
    while True:
        newdata = ser.readline()
        n_data = newdata.decode('latin-1')
        if n_data[0:6] == '$GPRMC':
            newmsg = pynmea2.parse(n_data)
            lat = newmsg.latitude
            lng = newmsg.longitude

            if lat != 0 and lng != 0:
                last_valid_lat = lat
                last_valid_lng = lng
                gps = {"LAT": lat, "LNG": lng}
                print(f"Latitude={lat} and Longitude={lng}")
                db.child("location").update(gps)
                print("Data sent")
            else:
                print("Invalid coordinates received. Sending last valid coordinates.")
                if last_valid_lat is not None and last_valid_lng is not None:
                    gps = {"LAT": last_valid_lat, "LNG": last_valid_lng}
                    db.child("location").update(gps)

        tracking_requested = db.child("trackingRequested").get().val()
        if tracking_requested:
            user_input = input("Family requested tracking. Allow tracking? (yes/no): ")
            if user_input.lower() == "yes":
                db.update({"trackingConfirmed": True})
                db.update({"trackingRequested": False})
            else:
                db.update({"trackingConfirmed": False})
                db.update({"trackingRequested": False})
                print("Tracking request denied.")
finally:
    cleanup()

