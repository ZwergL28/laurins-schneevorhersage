import requests
import pandas as pd

LAT = 47.57
LON = 7.66

def load_forecast(lat=LAT, lon=LON):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "snowfall,temperature_2m,precipitation",
        "timezone": "Europe/Zurich"
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def to_table(data):
    hourly = data["hourly"]
    df = pd.DataFrame({
        "time": pd.to_datetime(hourly["time"]),
        "snowfall_cm": hourly["snowfall"],
        "temp_c": hourly["temperature_2m"],
        "precip_mm": hourly["precipitation"]
    })
    return df

def will_it_snow_between(df, start_date, end_date):
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) + pd.Timedelta(days=1)  # end_date inklusive

    mask = (df["time"] >= start) & (df["time"] < end)
    window = df.loc[mask].copy()

    # "Schneit" = snowfall > 0
    snow_hours = window[window["snowfall_cm"] > 0]

    will_snow = not snow_hours.empty
    total_snow_cm = snow_hours["snowfall_cm"].sum()

    return will_snow, total_snow_cm, snow_hours, window

if __name__ == "__main__":
    data = load_forecast()
    df = to_table(data)

    will_snow, total_snow_cm, snow_hours, window = will_it_snow_between(
        df, "2025-12-16", "2025-12-25"
    )

    print("Schneit es irgendwann zwischen 16.12. und 25.12.? ->", will_snow)
    print("Summe Schneefall in diesem Zeitraum (cm):", round(total_snow_cm, 2))

    if will_snow:
        print("\nStunden mit Schneefall:")
        print(snow_hours[["time", "snowfall_cm", "temp_c"]].head(20))
    else:
        print("\nKeine Stunden mit Schneefall in der Vorhersage gefunden.")
        