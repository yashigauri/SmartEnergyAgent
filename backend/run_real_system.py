import serial
import json
import requests

# 🔁 CHANGE COM PORT IF NEEDED
import serial
import time

print("Connecting to COM5...")

time.sleep(2)  # give time after plugging

ser = serial.Serial()
ser.port = 'COM5'
ser.baudrate = 9600
ser.timeout = 1

ser.open()

print("Connected to COM5!")

print("🚀 Sending data to Flask...\n")

while True:
    try:
        line = ser.readline().decode().strip()
        data = json.loads(line)

        payload = {
            "temp_c": data["temp"],
            "humidity": data["hum"],
            "occupied": data["motion"] == 1
        }

        # 🔥 SEND TO FLASK
        requests.post("http://127.0.0.1:5000/api/sensor_push", json=payload)

        print("Sent:", payload)

    except Exception as e:
        print("Error:", e)