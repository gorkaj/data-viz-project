import os
from dotenv import load_dotenv
import requests
import csv
from datetime import datetime

# Set up API
load_dotenv("../.env")
OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
BASE_URL = "https://api.openaq.org/v3/"
DATA_ROOT = "../data/"
headers = {
    "X-API-Key": OPENAQ_API_KEY
}

# Populate sensors.csv
lat, long = 56.175226574052786, 10.17011443955166  # Aarhus, use 25 km
# lat, long = 12.968905302543678, 77.57254360290341  # Bengaluru, use 5 km


valid_pollutants = {"pm10", "pm25", "o3", "no2", "co", "so2"}
response = requests.get(
    BASE_URL + "locations",
    params={"coordinates": f"{lat},{long}", "radius": 25000},
    headers=headers)

with open(DATA_ROOT + "sensors.csv", "a", newline="", encoding="utf-8") as f:
    rows = 0
    writer = csv.writer(f)
    if not os.path.isfile(DATA_ROOT + "sensors.csv"):
        writer.writerow(
            ["sensor_id", "country", "latitude", "longitude", "pollutant_type", "first_reading", "last_reading", "unit"])

    for location in response.json().get("results", []):
        country_name = location["country"]["name"]
        latitude = location["coordinates"]["latitude"]
        longitude = location["coordinates"]["longitude"]
        if not location["datetimeFirst"] or not location["datetimeLast"]:
            continue
        first_reading = location["datetimeFirst"]["utc"]
        last_reading = location["datetimeLast"]["utc"]

        if datetime.fromisoformat(last_reading.replace("Z", "+00:00")).year < 2025:
            continue

        for sensor in location.get("sensors", []):
            pollutant_type = sensor["parameter"]["name"].lower()
            unit = sensor["parameter"]["units"]

            if pollutant_type not in valid_pollutants:
                continue

            rows += 1
            sensor_id = sensor["id"]

            writer.writerow([
                sensor_id,
                country_name,
                latitude,
                longitude,
                pollutant_type,
                first_reading,
                last_reading,
                unit
            ])

    print(f"Saved rows: {rows}")
