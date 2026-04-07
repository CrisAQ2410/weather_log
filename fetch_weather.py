"""
fetch_weather.py
Tự động fetch dữ liệu thời tiết thực từ Open-Meteo API và lưu vào CSV.
Chạy hàng ngày qua GitHub Actions.
"""

import json
import csv
import os
import sys
from datetime import datetime, timezone
from urllib.request import urlopen

LOCATIONS = [
    {"name": "Hanoi",       "lat": 21.0245, "lon": 105.8412},
    {"name": "Ho_Chi_Minh", "lat": 10.8231, "lon": 106.6297},
    {"name": "Da_Nang",     "lat": 16.0544, "lon": 108.2022},
]

DATA_DIR = "data/weather"

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]


def fetch_weather(lat, lon):
    vars_str = ",".join(HOURLY_VARS)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly={vars_str}"
        f"&forecast_days=1"
        f"&timezone=Asia%2FBangkok"
    )
    print(f"  GET {url}")
    with urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    print(f"  Response keys: {list(data.keys())}")
    return data


def extract_current_hour(data):
    hourly = data["hourly"]
    now_hour = datetime.now().strftime("%Y-%m-%dT%H:00")
    times = hourly["time"]
    idx = 0
    for i, t in enumerate(times):
        if t <= now_hour:
            idx = i
    row = {"time": times[idx]}
    for var in HOURLY_VARS:
        row[var] = hourly[var][idx]
    return row


def append_to_csv(filepath, row):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file_exists = os.path.isfile(filepath)
    fieldnames = ["fetched_at", "time"] + HOURLY_VARS
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    print(f"=== Weather Fetch @ {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    success_count = 0

    for loc in LOCATIONS:
        name = loc["name"]
        print(f"\nFetching {name}...")
        try:
            raw = fetch_weather(loc["lat"], loc["lon"])
            row = extract_current_hour(raw)
            row["fetched_at"] = fetched_at

            csv_path = os.path.join(DATA_DIR, f"{name}.csv")
            append_to_csv(csv_path, row)
            print(f"  Saved -> {csv_path}")
            print(f"  Temp={row['temperature_2m']}C  Humidity={row['relative_humidity_2m']}%  Wind={row['wind_speed_10m']}km/h")
            success_count += 1

        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}", file=sys.stderr)
            raise  # Làm workflow fail rõ ràng thay vì âm thầm

    print(f"\n=== Done: {success_count}/{len(LOCATIONS)} locations ===")


if __name__ == "__main__":
    main()
