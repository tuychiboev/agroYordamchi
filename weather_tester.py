import requests
from datetime import datetime

# Coordinates for Pop (Pap), Namangan, Uzbekistan
LAT = 40.8736
LON = 71.0256

# Map Open-Meteo weather codes to human-readable text
# Based on WMO standard used by Open-Meteo
WEATHER_CODE_MAP = {
    0: "sunny / clear sky",
    1: "mostly sunny",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}

def weather_code_to_text(code):
    if code is None or code == "-":
        return "unknown"
    return WEATHER_CODE_MAP.get(int(code), f"code {code}")

def get_daily_forecast(requested_days: int):
    """
    Fetch daily forecast from Open-Meteo.
    Open-Meteo supports up to 16 days; clamp if user asked for more.
    """
    # Clamp to Open-Meteo limit
    days = min(requested_days, 16)

    # Build API URL
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&daily=weathercode,temperature_2m_max,temperature_2m_min,"
        "precipitation_sum,windspeed_10m_max"
        "&timezone=Asia/Tashkent"
        f"&forecast_days={days}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("❌ Failed to fetch data from Open-Meteo:")
        print(e)
        return

    data = resp.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_sum", [])
    wind = daily.get("windspeed_10m_max", [])
    codes = daily.get("weathercode", [])

    print("\n--- Forecast ---")

    max_available = min(days, len(dates))

    for i in range(max_available):
        # Convert 2025-11-20 -> 20/11
        try:
            dt = datetime.strptime(dates[i], "%Y-%m-%d")
            date_str = dt.strftime("%d/%m")
        except Exception:
            date_str = dates[i]

        desc = weather_code_to_text(codes[i] if i < len(codes) else None)
        max_temp = tmax[i] if i < len(tmax) else "?"
        min_temp = tmin[i] if i < len(tmin) else "?"
        rain_mm = rain[i] if i < len(rain) else "?"
        wind_kmh = wind[i] if i < len(wind) else "?"

        print(
            f"- {date_str}: {desc}, "
            f"day {max_temp}°C, night {min_temp}°C, "
            f"wind {wind_kmh} km/h, rain {rain_mm} mm"
        )

    if requested_days > 16:
        print(
            "\nℹ️ Note: Open-Meteo's standard forecast API only supports up to 16 days. "
            "You requested "
            f"{requested_days} days, so only the next {days} days were fetched."
        )

    print("\nDone.")

def main():
    print("Weather Forecast for Pop, Namangan (Open-Meteo)")
    try:
        days = int(input("Enter number of days (1–30): ").strip())
    except ValueError:
        print("❌ Please enter a valid integer.")
        return

    if not 1 <= days <= 30:
        print("❌ Please enter a number between 1 and 30.")
        return

    get_daily_forecast(days)

if __name__ == "__main__":
    main()
