import os
from dotenv import load_dotenv
import requests
import pandas as pd
import datetime

def to_utc_str(dt: datetime.datetime) -> str:
    """Format datetime as an ISO string without microseconds, with Z."""
    return dt.replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_measurements(sensor_id, start_date, end_date):
    """Fetch daily measurements from OpenAQ API for a sensor."""
    url = OPENAQ_BASE_URL.format(sensor_id=sensor_id)
    all_results = []
    params = {
        "datetime_from": to_utc_str(start_date),
        "datetime_to": to_utc_str(end_date),
        "limit": 1000,
        "page": 1
    }

    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"OPENAQ API error: {resp.status_code}, {resp.text}")
            break

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for r in results:
            ts = datetime.datetime.fromisoformat(r["period"]["datetimeFrom"]["utc"].replace("Z", "+00:00"))

            # keep only 00:00, 06:00, 12:00, 18:00
            if ts.hour in [0, 6, 12, 18]:
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


def keep_sample_hours(df, hours):
    """Keep only rows at specified hours."""
    return df[df.index.hour.isin(hours)]


def fetch_weather(lat, lon, timestamp):
    """Fetch weather (wind_speed, rain) for a given lat / lon and timestamp."""
    url = WEATHER_BASE_URL.format(lat=lat, lon=lon, start=int(timestamp), apikey=WEATHER_API_KEY)
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Weather API error: {resp.status_code}, {resp.text}")
        return {"wind_speed": 0, "rain": 0}

    data = resp.json()
    results = data.get("list", [])[0]

    wind_speed = results.get("wind", None)
    wind_speed = wind_speed.get("speed", 0) if wind_speed else 0
    rain = 0
    if "rain" in results:
        rain = results["rain"].get("1h", 0)

    return {
        "wind_speed": wind_speed,
        "rain": rain
    }


# SETUP
load_dotenv("../.env")
OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
OPENAQ_BASE_URL = "https://api.openaq.org/v3/sensors/{sensor_id}/measurements/hourly"

WEATHER_API_KEY = os.getenv('OPEN_WEATHER_API_KEY')
WEATHER_BASE_URL = "https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&cnt=1&appid={apikey}"

DATA_ROOT = "../data/"
INPUT_FILE = DATA_ROOT + "sensors.csv"
OUTPUT_FILE = DATA_ROOT + "readings.csv"
headers = {
    "X-API-Key": OPENAQ_API_KEY
}

# Read sensors and call for data
sensors_df = pd.read_csv(INPUT_FILE)
all_data = []

for _, row in sensors_df.iterrows():
    sensor_id = row["sensor_id"]
    lat = row["latitude"]
    lon = row["longitude"]

    # first_reading = datetime.datetime.fromisoformat(
    #     row["first_reading"].replace("Z", "+00:00")
    # )
    yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    first_reading = yesterday - datetime.timedelta(days=90)

    print(f"Fetching sensor {sensor_id} from {first_reading.isoformat()} to {yesterday.isoformat()}")

    results = fetch_measurements(sensor_id, first_reading, yesterday)
    print(f"Fetched {len(results)} readings")

    for r in results:
        ts = datetime.datetime.fromisoformat(r["reading_datetime"].replace("Z", "+00:00"))

        if ts.hour in [0, 6, 12, 18]:
            weather = fetch_weather(lat, lon, ts.timestamp())
            r["wind_speed"] = weather["wind_speed"]
            r["rain"] = weather["rain"]

    all_data.extend(results)


df_final = pd.DataFrame(all_data)
df_final.to_csv(OUTPUT_FILE, index=False)
print(f"Saved {len(df_final)} rows to {OUTPUT_FILE}")

