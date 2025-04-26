from flask import Flask, send_file, render_template
import asyncio
from bleak import BleakScanner, BleakClient
import csv
from datetime import datetime
import threading
import time
from google import genai
import pandas as pd

app = Flask(__name__)

GEMINI_CSV_FILE = "gemini_data.csv"
GEMINI_API_KEY = "your_API_key"
CSV_FILE = "data.csv"
HEALTH_CSV_FILE = 'health.csv'
BLE_DEVICE_NAME = "PlantSensor"
SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
CHARACTERISTIC_UUID = "abcd1234-abcd-1234-abcd-1234567890ab"

# Initialize CSV file with header if it doesn't exist
try:
    with open(CSV_FILE, "x", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature", "Humidity", "Moisture", "Soilph"])
except FileExistsError:
    pass

# Initialize health.CSV file with header if it doesn't exist
try:
    with open(HEALTH_CSV_FILE, "x", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Health"])
except FileExistsError:
    pass

def log_to_csv(temperature, humidity, moisture, soilph):
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), temperature, humidity, moisture, soilph])

def log_health(health):
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), health])

client = genai.Client(api_key=GEMINI_API_KEY)

# Create CSV for Gemini responses if not exists
try:
    with open(GEMINI_CSV_FILE, "x", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Response"])
except FileExistsError:
    pass

def generate_gemini_prompt(temperature, humidity, moist, soilph):
    return f"""
You are an expert in gardening and plant care.

Here is the current garden sensor data of of my garden:
- Soil pH: {soilph}%
- Air Humidity: {humidity}%
- Soil temperature: {temperature}%
- Soil moisture: {moist}%

Please:
1. Act as you are a garden talking to me and Describe the gardens condition based on this data in a paragraph also suggest me any fertilizers if I had to use and why should I use,
 give it as a plain text without any bold or italics.
"""

def generate_health(temperature, humidity, moist, soilph):
    return f"""
You are an expert in gardening and plant care.

Here is the current garden sensor data of of my garden:
- Soil pH: {soilph}%
- Air Humidity: {humidity}%
- Soil temperature: {temperature}%
- Soil moisture: {moist}%

Please:
1. give me the health of my garden based on the sensor data that I have given. give me the result out of 100 and give me only the number. I am using your output in my 
frontend website so give me only the number out of 100. 

"""

async def run_gemini_for_garden():
    while True:
        try:
            with open(CSV_FILE, "r") as f:
                last_line = f.readlines()[-1].strip().split(",")
                temperature = last_line[1]
                humidity = last_line[2]
                moist = last_line[3]
                soilph = last_line[4]
        except Exception as e:
            print(f"Failed to read BLE CSV: {e}")
            await asyncio.sleep(30)
            continue

        prompt = generate_gemini_prompt(temperature, humidity, moist, soilph)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            reply = response.text.strip()
            # print("Gemini Response:", reply)
            with open(GEMINI_CSV_FILE, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now(), reply])
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        await asyncio.sleep(30)

async def run_gemini_health():
    while True:
        try:
            with open(CSV_FILE, "r") as f:
                last_line = f.readlines()[-1].strip().split(",")
                temperature = last_line[1]
                humidity = last_line[2]
                moist = last_line[3]
                soilph = last_line[4]
        except Exception as e:
            print(f"Failed to read BLE CSV: {e}")
            await asyncio.sleep(30)
            continue

        prompt = generate_health(temperature, humidity, moist, soilph)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            reply = response.text.strip()
            # print("Gemini Response:", reply)
            with open(HEALTH_CSV_FILE, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now(), reply])
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        await asyncio.sleep(30)


async def connect_to_device():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    plant_sensor = next((d for d in devices if d.name == BLE_DEVICE_NAME), None)

    if not plant_sensor:
        print("ESP32 not found. Make sure it's powered on and advertising.")
        return None

    print(f"Found {plant_sensor.name} ({plant_sensor.address}). Connecting...")

    try:
        client = BleakClient(plant_sensor.address)
        await client.connect()

        if client.is_connected:
            print("Connected to ESP32.")
            return client
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

async def read_ble_data():
    while True:
        client = await connect_to_device()
        print(client.is_connected)
        if client:
            def handle_data(sender, data):
                try:
                    text = data.decode()
                    print(f"Received: {text}")
                    temperature, humidity, moisture, soilph = text.split(",")
                    log_to_csv(temperature, humidity, moisture, soilph)
                except Exception as e:
                    print(f"Error handling data: {e}")
                

            await client.start_notify(CHARACTERISTIC_UUID, handle_data)

            # Wait and keep the connection alive until it drops
            while client.is_connected:
                await asyncio.sleep(20)

            print("Disconnected from ESP32.")

        print("Reattempting BLE connection in 5 seconds...")
        await asyncio.sleep(5)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/data")
def get_data():
    return send_file(CSV_FILE)

@app.route("/health")
def get_health():
    return send_file(HEALTH_CSV_FILE)

@app.route("/gemini")
def get_gemini_data():
    try:
        run_gemini_for_garden()
        # Load the CSV file
        df = pd.read_csv("gemini_data.csv", parse_dates=["Timestamp"], encoding="latin1")

        # Get the row with the latest timestamp
        latest_row = df.loc[df["Timestamp"].idxmax()]
        timestamp = latest_row["Timestamp"].strftime("%H:%M:%S")

        # Access the response
        latest_response = latest_row["Response"]
        print(type(latest_row))

        return {"response": str(latest_response)}

    except:
        return {"response": "No response from the garden yet, maybe its sleeping. Tryagain after sometime!"}


@app.route("/update-gemini")
def update_gemini():
    try:
        # Load the CSV file
        df = pd.read_csv("gemini_data.csv", parse_dates=["Timestamp"], encoding="latin1")

        # Get the row with the latest timestamp
        latest_row = df.loc[df["Timestamp"].idxmax()]
        timestamp = latest_row["Timestamp"].strftime("%H:%M:%S")

        # Access the response
        latest_response = latest_row["Response"]
        print(type(latest_row))

        return {"response": str(latest_response)}

    except:
        return {"response": "No response from the garden yet, maybe its sleeping. Tryagain after sometime!"}


if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(read_ble_data()), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_gemini_for_garden()), daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_gemini_health()), daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)

