import os
from dotenv import load_dotenv
import requests
import csv

# Set up API
load_dotenv("../.env")
OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
BASE_URL = "https://api.openaq.org/v3/"
DATA_ROOT = "../data/"
headers = {
    "X-API-Key": OPENAQ_API_KEY
}

# Populate sensors.csv
lat, long = 56.175226574052786, 10.17011443955166

response = requests.get(
    BASE_URL + "locations",
    params={"coordinates": f"{lat},{long}", "radius": 25000},
    headers=headers)

with open(DATA_ROOT + "sensors.csv", "w", newline="", encoding="utf-8") as f:
    rows = 0
    writer = csv.writer(f)
    writer.writerow(["sensor_id", "country", "latitude", "longitude", "pollutant_type", "first_reading", "last_reading"])

    for location in response.json()["results"]:
        country_name = location["country"]["name"]
        latitude = location["coordinates"]["latitude"]
        longitude = location["coordinates"]["longitude"]
        if not location["datetimeFirst"] or not location["datetimeLast"]:
            continue
        first_reading = location["datetimeFirst"]["utc"]
        last_reading = location["datetimeLast"]["utc"]

        for sensor in location["sensors"]:

            rows += 1
            sensor_id = sensor["id"]
            pollutant_type = sensor["parameter"]["name"]

            writer.writerow([
                sensor_id,
                country_name,
                latitude,
                longitude,
                pollutant_type,
                first_reading,
                last_reading
            ])
    print(f"Saved rows: {rows}")
