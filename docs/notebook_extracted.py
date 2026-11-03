# --- Cell 0 ---
from kaggle_secrets import UserSecretsClient

user_secrets = UserSecretsClient()

OPENAQ_API_KEY = user_secrets.get_secret("OPENAQ_API_KEY")

print("API key loaded:", OPENAQ_API_KEY is not None)

# --- Cell 1 ---
import requests

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

url = "https://api.openaq.org/v3/locations"

params = {
    "coordinates": "18.5204,73.8567",
    "radius": 25000,
    "parameters_id": 2,
    "limit": 100
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Status:", response.status_code)

# --- Cell 2 ---
data = response.json()

print("Number of locations:", len(data["results"]))

for location in data["results"]:
    print(
        location["id"],
        "|",
        location["name"],
        "|",
        location["coordinates"]
    )

# --- Cell 3 ---
import pprint

pprint.pp(data["results"][0])

# --- Cell 4 ---
import requests
import pandas as pd

sensor_id = 5354

url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

params = {
    "limit": 1000
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Status:", response.status_code)

# --- Cell 5 ---
data = response.json()

print(data.keys())

# --- Cell 6 ---
print("Number of records:", len(data["results"]))

print(data["results"][0])

# --- Cell 7 ---
df = pd.json_normalize(data["results"])

df.head()

# --- Cell 8 ---


pm25 = df[
    [
        "value",
        "period.datetimeFrom.utc"
    ]
].copy()

pm25.columns = ["pm25", "timestamp"]

pm25.head()

# --- Cell 9 ---
pm25["timestamp"] = pd.to_datetime(
    pm25["timestamp"],
    utc=True
)

pm25.head()

# --- Cell 10 ---
pm25["timestamp"] = pm25["timestamp"].dt.tz_convert(
    "Asia/Kolkata"
)

pm25.head()

# --- Cell 11 ---
pm25["date"] = pm25["timestamp"].dt.date

pm25.head()

# --- Cell 12 ---
print("Rows:", len(pm25))
print("Start:", pm25["timestamp"].min())
print("End:", pm25["timestamp"].max())

# --- Cell 13 ---
pm25["pm25"].describe()

# --- Cell 14 ---
daily_pm25 = (
    pm25
    .groupby("date")["pm25"]
    .mean()
    .reset_index()
)

daily_pm25.head()

# --- Cell 15 ---
daily_pm25.shape

# --- Cell 16 ---
daily_pm25["pm25"].describe()

# --- Cell 17 ---
import matplotlib.pyplot as plt

# --- Cell 18 ---
plt.figure(figsize=(15, 5))

plt.plot(
    daily_pm25["date"],
    daily_pm25["pm25"]
)

plt.xlabel("Date")
plt.ylabel("PM2.5 (µg/m³)")
plt.title("Daily PM2.5 — AAQMS Karve Road, Pune")

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# --- Cell 19 ---
print("Rows:", len(pm25))
print("Start:", pm25["timestamp"].min())
print("End:", pm25["timestamp"].max())

daily_pm25["pm25"].describe()

# --- Cell 20 ---
import requests
import pandas as pd
import time

sensor_id = 5354

url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

all_data = []

start_date = "2017-01-01T00:00:00Z"
end_date = "2018-01-01T00:00:00Z"

params = {
    "datetime_from": start_date,
    "datetime_to": end_date,
    "limit": 1000
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Status:", response.status_code)

data = response.json()

print("Records:", len(data["results"]))

# --- Cell 21 ---
print(data.keys())

# --- Cell 22 ---
print(data.get("meta"))

# --- Cell 23 ---
import requests
import pandas as pd
import time

sensor_id = 5354

url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

all_records = []

for page in range(1, 20):

    params = {
        "datetime_from": "2017-01-01T00:00:00Z",
        "datetime_to": "2018-01-01T00:00:00Z",
        "limit": 1000,
        "page": page
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    print(f"Page {page}: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        break

    result = response.json()["results"]

    print(f"  Records: {len(result)}")

    if len(result) == 0:
        break

    all_records.extend(result)

    # If fewer than 1000, we've reached the last page
    if len(result) < 1000:
        break

    time.sleep(0.2)

print("Total records:", len(all_records))

# --- Cell 24 ---
pm25_raw = pd.json_normalize(all_records)

pm25 = pm25_raw[["value", "period.datetimeFrom.utc"]].copy()

pm25.columns = ["pm25", "timestamp"]

pm25["timestamp"] = pd.to_datetime(
    pm25["timestamp"],
    utc=True
)

# Convert UTC → Indian Standard Time
pm25["timestamp"] = pm25["timestamp"].dt.tz_convert("Asia/Kolkata")

# Extract date
pm25["date"] = pm25["timestamp"].dt.date

# Daily average PM2.5
daily_pm25 = (
    pm25.groupby("date")["pm25"]
    .agg(["mean", "count"])
    .reset_index()
)

daily_pm25.columns = ["date", "pm25", "measurements"]

daily_pm25.head()

# --- Cell 25 ---
daily_pm25 = daily_pm25[
    daily_pm25["measurements"] >= 12
].copy()

print("Number of valid days:", len(daily_pm25))
print(daily_pm25["pm25"].describe())

# --- Cell 26 ---
import matplotlib.pyplot as plt

plt.figure(figsize=(15, 5))

plt.plot(
    daily_pm25["date"],
    daily_pm25["pm25"]
)

plt.xlabel("Date")
plt.ylabel("Daily Average PM2.5 (µg/m³)")
plt.title("Daily PM2.5 — Karve Road, Pune")
plt.xticks(rotation=45)
plt.grid(True)
plt.show()

# --- Cell 27 ---
print("Number of valid days:", len(daily_pm25))
print(daily_pm25["pm25"].describe())

# --- Cell 28 ---
import requests
import pandas as pd

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

url = "https://api.openaq.org/v3/locations"

params = {
    "coordinates": "18.5204,73.8567",
    "radius": 25000,
    "parameters_id": 2,   # PM2.5
    "limit": 100
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Status:", response.status_code)

locations = response.json()["results"]

print("Number of locations:", len(locations))

# --- Cell 29 ---
import pandas as pd

station_info = []

for loc in locations:
    station_info.append({
        "id": loc["id"],
        "name": loc["name"],
        "provider": loc.get("provider", {}).get("name"),
        "latitude": loc["coordinates"]["latitude"],
        "longitude": loc["coordinates"]["longitude"],
        "first": loc.get("datetimeFirst", {}).get("utc"),
        "last": loc.get("datetimeLast", {}).get("utc")
    })

stations = pd.DataFrame(station_info)

stations = stations.sort_values(
    "last",
    ascending=False
)

print(stations[[
    "id",
    "name",
    "provider",
    "latitude",
    "longitude",
    "first",
    "last"
]].to_string(index=False))

# --- Cell 30 ---
location_id = 11613

url = f"https://api.openaq.org/v3/locations/{location_id}"

response = requests.get(
    url,
    headers={"X-API-Key": OPENAQ_API_KEY}
)

print("Status:", response.status_code)

location = response.json()

print("Station:", location["name"])

for sensor in location["sensors"]:
    print(
        "Sensor ID:", sensor["id"],
        "| Parameter:", sensor["parameter"]["name"],
        "| Units:", sensor["parameter"]["units"]
    )

# --- Cell 31 ---
location = response.json()["results"][0]

# --- Cell 32 ---
location = response.json()["results"][0]

print("Station:", location["name"])
print("Provider:", location["provider"]["name"])
print("Coordinates:", location["coordinates"])

print("\nPM2.5 sensors:")

for sensor in location["sensors"]:
    if sensor["parameter"]["name"] == "pm25":
        print(
            "Sensor ID:", sensor["id"],
            "| Name:", sensor["name"]
        )

# --- Cell 33 ---
pm25_sensors = [12236463, 39466]

for sensor_id in pm25_sensors:
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}"

    response = requests.get(
        url,
        headers={"X-API-Key": OPENAQ_API_KEY}
    )

    print("\nSensor:", sensor_id)
    print("Status:", response.status_code)

    sensor = response.json()["results"][0]

    print("First:", sensor.get("datetimeFirst"))
    print("Last:", sensor.get("datetimeLast"))

# --- Cell 34 ---
import requests
import time
import pandas as pd

sensor_id = 12236463

url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

all_records = []

for page in range(1, 30):

    params = {
        "datetime_from": "2025-02-18T00:00:00Z",
        "datetime_to": "2026-10-14T00:00:00Z",
        "limit": 1000,
        "page": page
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    print(f"Page {page}: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        break

    records = response.json()["results"]

    print("  Records:", len(records))

    if len(records) == 0:
        break

    all_records.extend(records)

    if len(records) < 1000:
        break

    time.sleep(0.2)

print("\nTotal records:", len(all_records))

# --- Cell 35 ---
pm25_raw = pd.json_normalize(all_records)

print("Shape:", pm25_raw.shape)
print(pm25_raw.columns.tolist())

# --- Cell 36 ---
pm25 = pm25_raw[
    ["value", "period.datetimeFrom.utc"]
].copy()

pm25.columns = ["pm25", "timestamp"]

# Convert UTC timestamps
pm25["timestamp"] = pd.to_datetime(
    pm25["timestamp"],
    utc=True
)

# Convert to Indian Standard Time
pm25["timestamp"] = pm25["timestamp"].dt.tz_convert(
    "Asia/Kolkata"
)

# Extract local date
pm25["date"] = pm25["timestamp"].dt.date

# Daily aggregation
daily_pm25 = (
    pm25.groupby("date")["pm25"]
    .agg(["mean", "count"])
    .reset_index()
)

daily_pm25.columns = [
    "date",
    "pm25",
    "measurements"
]

print(daily_pm25.head())
print("\nNumber of days:", len(daily_pm25))

# --- Cell 37 ---
daily_pm25 = daily_pm25[
    daily_pm25["measurements"] >= 12
].copy()

print("Valid days:", len(daily_pm25))
print(daily_pm25["pm25"].describe())

# --- Cell 38 ---
print("Start:", daily_pm25["date"].min())
print("End:", daily_pm25["date"].max())

# --- Cell 39 ---
print(daily_pm25.isna().sum())

# --- Cell 40 ---
print("Start date:", daily_pm25["date"].min())
print("End date:", daily_pm25["date"].max())

print("\nNumber of valid days:", len(daily_pm25))

print("\nPM2.5 statistics:")
print(daily_pm25["pm25"].describe())

# --- Cell 41 ---
daily_pm25.head()

# --- Cell 42 ---
daily_pm25.tail()

# --- Cell 43 ---
import requests
import pandas as pd

start_date = str(daily_pm25["date"].min())
end_date = str(daily_pm25["date"].max())

latitude = 18.530085
longitude = 73.849598

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": start_date,
    "end_date": end_date,
    "daily": [
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_mean",
        "wind_direction_10m_dominant",
        "surface_pressure_mean"
    ],
    "timezone": "Asia/Kolkata"
}

response = requests.get(url, params=params)

print("Status:", response.status_code)

# --- Cell 44 ---
weather_data = response.json()

weather = pd.DataFrame({
    "date": weather_data["daily"]["time"],
    "temperature": weather_data["daily"]["temperature_2m_mean"],
    "humidity": weather_data["daily"]["relative_humidity_2m_mean"],
    "precipitation": weather_data["daily"]["precipitation_sum"],
    "wind_speed": weather_data["daily"]["wind_speed_10m_mean"],
    "wind_direction": weather_data["daily"]["wind_direction_10m_dominant"],
    "pressure": weather_data["daily"]["surface_pressure_mean"]
})

weather["date"] = pd.to_datetime(weather["date"]).dt.date

print(weather.shape)
weather.head()

# --- Cell 45 ---
df = pd.merge(
    daily_pm25,
    weather,
    on="date",
    how="inner"
)

print("Shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isna().sum())

df.head()

# --- Cell 46 ---
df.to_csv("pune_pm25_weather.csv", index=False)

print("Saved:", df.shape)

# --- Cell 47 ---
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))

plt.hist(df["pm25"], bins=30)

plt.xlabel("PM2.5")
plt.ylabel("Number of days")
plt.title("Distribution of Daily PM2.5 - Pune")

plt.show()

# --- Cell 48 ---
plt.figure(figsize=(14, 5))

plt.plot(df["date"], df["pm25"])

plt.xlabel("Date")
plt.ylabel("PM2.5")
plt.title("Daily PM2.5 Trend - Revenue Colony, Pune")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

# --- Cell 49 ---
correlations = (
    df.select_dtypes("number")
      .corr()["pm25"]
      .sort_values(ascending=False)
)

print(correlations)

# --- Cell 50 ---
!pip install -q earthengine-api

# --- Cell 51 ---
import ee

ee.Authenticate()

# --- Cell 52 ---
ee.Initialize(project="pune-air-quality")

# --- Cell 53 ---
print(
    ee.String("Earth Engine connected!")
    .getInfo()
)

# --- Cell 54 ---
import ee

aod_collection = (
    ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
    .select("Optical_Depth_055")
)

start_date = str(df["date"].min())
end_date = str(df["date"].max())

print("Date range:", start_date, "to", end_date)

image_count = (
    aod_collection
    .filterDate(start_date, end_date)
    .size()
    .getInfo()
)

print("MODIS images:", image_count)

# --- Cell 55 ---
latitude = 18.530085
longitude = 73.849598

point = ee.Geometry.Point([
    longitude,
    latitude
])

print("Pune point created")

# --- Cell 56 ---
import pandas as pd

test_date = str(df["date"].min())

next_date = str(
    pd.to_datetime(test_date) + pd.Timedelta(days=1)
)

image = (
    aod_collection
    .filterDate(test_date, next_date)
    .filterBounds(point)
    .first()
)

print("Test date:", test_date)
print("Image found:", image is not None)

# --- Cell 57 ---
import pandas as pd
import ee

latitude = 18.530085
longitude = 73.849598

point = ee.Geometry.Point([
    longitude,
    latitude
])

test_date = str(df["date"].min())

next_date = (
    pd.to_datetime(test_date) + pd.Timedelta(days=1)
).strftime("%Y-%m-%d")

print("Location:", latitude, longitude)
print("Start date:", test_date)
print("End date:", next_date)

# --- Cell 58 ---
image = (
    aod_collection
    .filterDate(test_date, next_date)
    .filterBounds(point)
    .first()
)

print("Image found:", image is not None)

# --- Cell 59 ---
aod_value = image.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=point,
    scale=1000
).get("Optical_Depth_055")

raw_value = aod_value.getInfo()

print("Raw AOD:", raw_value)

if raw_value is not None:
    scaled_aod = raw_value * 0.001
    print("Scaled AOD:", scaled_aod)
else:
    print("No valid AOD available for this date.")

# --- Cell 60 ---
aod_collection = (
    ee.ImageCollection("MODIS/061/MCD19A2_GRANULES")
    .filterBounds(point)
    .select("Optical_Depth_055")
)

print("AOD collection ready")

# --- Cell 61 ---
test_date = str(df["date"].min())

next_date = (
    pd.to_datetime(test_date) + pd.Timedelta(days=1)
).strftime("%Y-%m-%d")

daily_images = (
    aod_collection
    .filterDate(test_date, next_date)
)

print("Images covering Pune:", daily_images.size().getInfo())

# --- Cell 62 ---
daily_aod_image = daily_images.mean()

aod_value = daily_aod_image.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=point,
    scale=1000,
    bestEffort=True
).get("Optical_Depth_055")

raw_value = aod_value.getInfo()

print("Raw AOD:", raw_value)

if raw_value is not None:
    print("Scaled AOD:", raw_value * 0.001)
else:
    print("Still no valid AOD for this date.")

# --- Cell 63 ---
import ee
import pandas as pd

# Get all dates from our PM2.5 + weather dataset
dates = df["date"].tolist()

def get_daily_aod(date):
    start = ee.Date(str(date))
    end = start.advance(1, "day")

    images = (
        aod_collection
        .filterDate(start, end)
        .filterBounds(point)
    )

    # Average all MODIS observations for that day
    daily_image = images.mean()

    # Extract AOD at Pune station
    value = daily_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=1000,
        bestEffort=True
    ).get("Optical_Depth_055")

    # Apply MODIS scale factor
    return ee.Number(value).multiply(0.001)


# Create an Earth Engine Feature for every date
features = []

for date in dates:
    feature = ee.Feature(
        None,
        {
            "date": str(date),
            "aod": get_daily_aod(date)
        }
    )
    features.append(feature)

collection = ee.FeatureCollection(features)

print("Requesting AOD data from Earth Engine...")

aod_result = collection.getInfo()

print("AOD extraction complete!")
print("Records:", len(aod_result["features"]))

