import os
from dotenv import load_dotenv
import requests
import pandas as pd
import datetime

def fetch_measurements(sensor_id, start_date, end_date):
    """Fetch daily measurements from OpenAQ API for a sensor."""
    url = BASE_URL.format(sensor_id=sensor_id)
    params = {
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "limit": 1000,
        "page": 1
    }
    all_results = []

    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise Exception(f"API error: {resp.status_code}, {resp.text}")

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for r in results:
            all_results.append({
                "reading_datetime": r["period"]["datetimeFrom"]["utc"],
                "sensor_id": sensor_id,
                "reading_value": r["value"]
            })

        # Pagination
        meta = data.get("meta", {})
        found = meta.get("found", 0)
        limit = meta.get("limit", len(results))
        page = meta.get("page", params["page"])

        if page * limit >= found:
            break

        params["page"] = page + 1

    return all_results


# Set up API
load_dotenv("../.env")
API_KEY = os.getenv('API_KEY')
BASE_URL = "https://api.openaq.org/v3/sensors/{sensor_id}/measurements/daily"
DATA_ROOT = "../data/"
INPUT_FILE = DATA_ROOT + "sensors.csv"
OUTPUT_FILE = DATA_ROOT + "readings.csv"
headers = {
    "X-API-Key": API_KEY
}

# Read sensors and call for data
sensors_df = pd.read_csv(INPUT_FILE)
all_data = []

for _, row in sensors_df.iterrows():
    sensor_id = row["sensor_id"]

    first_reading = datetime.datetime.fromisoformat(
        row["first_reading"].replace("Z", "+00:00")
    )
    yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

    print(f"Fetching sensor {sensor_id} from {first_reading} to {yesterday}")

    results = fetch_measurements(sensor_id, first_reading, yesterday)
    if not results:
        print(f"No data for sensor {sensor_id}")
        continue
    all_data.extend(results)


df = pd.DataFrame(all_data)
df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved {len(df)} rows to {OUTPUT_FILE}")

