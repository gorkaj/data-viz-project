import os
import datetime
import requests
import pandas as pd
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time

# --- Setup ---
load_dotenv("../.env")
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

OPENAQ_BASE_URL = "https://api.openaq.org/v3/sensors/{sensor_id}/measurements/hourly"
WEATHER_BASE_URL = ("https://history.openweathermap.org/data/2.5/history/city" +
                    "?lat={lat}&lon={lon}&type=hour&start={start}&cnt=1&appid={apikey}&units=metric")
DATA_ROOT = "../data/"
INPUT_FILE = os.path.join(DATA_ROOT, "sensors.csv")
OUTPUT_FILE = os.path.join(DATA_ROOT, "readings.csv")

HEADERS = {"X-API-Key": OPENAQ_API_KEY}

start_date = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
end_date = datetime.datetime(2025, 9, 30, 23, 59, tzinfo=datetime.timezone.utc)

# --- Reuse a session for performance ---
session = requests.Session()
session.headers.update(HEADERS)

def to_utc_str(dt: datetime.datetime) -> str:
    return dt.replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_measurements(sensor_id, start_date, end_date, max_retries=5):
    url = OPENAQ_BASE_URL.format(sensor_id=sensor_id)
    all_results = []
    params = {
        "datetime_from": to_utc_str(start_date),
        "datetime_to": to_utc_str(end_date),
        "limit": 1000,
        "page": 1,
    }

    while True:
        for attempt in range(max_retries):
            try:
                resp = session.get(url, params=params, timeout=20)
                if resp.status_code == 408:
                    # Timeout
                    wait = 2 ** attempt
                    print(f"[OpenAQ] Timeout (408) for {sensor_id}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue

                if resp.status_code == 429:
                    wait = 2 ** attempt
                    print(f"[OpenAQ] Rate limit (429) for {sensor_id}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue

                if resp.status_code != 200:
                    print(f"[OpenAQ] Error {resp.status_code} for {sensor_id}: {resp.text[:200]}")
                    return all_results

                data = resp.json()
                break

            except requests.RequestException as e:
                wait = 2 ** attempt
                print(f"[OpenAQ] Network error for {sensor_id}: {e}, retrying in {wait}s...")
                time.sleep(wait)
        else:
            print(f"[OpenAQ] Failed after {max_retries} attempts for {sensor_id}. Skipping.")
            return all_results

        results = data.get("results", [])
        if not results:
            break

        for r in results:
            ts = datetime.datetime.fromisoformat(
                r["period"]["datetimeFrom"]["utc"].replace("Z", "+00:00")
            )
            if ts.hour in [0, 6, 12, 18]:
                all_results.append(
                    {
                        "reading_datetime": r["period"]["datetimeFrom"]["utc"],
                        "sensor_id": sensor_id,
                        "reading_value": r["value"],
                    }
                )

        meta = data.get("meta", {})
        page = meta.get("page", params["page"])
        limit = meta.get("limit", len(results))
        found = meta.get("found", 0)

        if page * limit >= found:
            break
        params["page"] = page + 1

    return all_results


@lru_cache(maxsize=5000)
def fetch_weather(lat, lon, timestamp):
    url = WEATHER_BASE_URL.format(lat=lat, lon=lon, start=int(timestamp), apikey=WEATHER_API_KEY)
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        print(f"[Weather] Error {resp.status_code}: {resp.text[:200]}")
        print(url)
        return {"wind_speed": 0, "rain": 0, "temp": 999}

    data = resp.json()
    if not data.get("list"):
        return {"wind_speed": 0, "rain": 0, "temp": 999}

    result = data["list"][0]
    return {
        "wind_speed": result.get("wind", {}).get("speed", 0),
        "rain": result.get("rain", {}).get("1h", 0),
        "temp": result.get("main", {}).get("temp", 999),
    }


def process_sensor(row):
    sensor_id = row["sensor_id"]
    lat, lon = row["latitude"], row["longitude"]
    print(f"Fetching sensor {sensor_id}...")

    results = fetch_measurements(sensor_id, start_date, end_date)
    for r in results:
        ts = datetime.datetime.fromisoformat(r["reading_datetime"].replace("Z", "+00:00"))
        weather = fetch_weather(round(lat, 2), round(lon, 2), int(ts.timestamp()))
        r.update(weather)
    return results


# --- Main ---
sensors_df = pd.read_csv(INPUT_FILE)
all_data = []

# Use threads for parallel fetching
MAX_WORKERS = min(5, len(sensors_df))
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_sensor, row) for _, row in sensors_df.iterrows()]
    for future in as_completed(futures):
        try:
            all_data.extend(future.result())
        except Exception as e:
            print("Error:", e)
        time.sleep(0.2)

# Save combined results
df_final = pd.DataFrame(all_data)
df_final.to_csv(OUTPUT_FILE, mode="a" if os.path.exists(OUTPUT_FILE) else "w", index=False, header=not os.path.exists(OUTPUT_FILE))
print(f"Saved {len(df_final)} rows to {OUTPUT_FILE}")
