import requests
from datetime import datetime

# ---------------------------------------------------------
# MULTILINGUAL WEATHER DESCRIPTIONS
# ---------------------------------------------------------
WEATHER_DESC = {
    "uz": {
        "Clear sky": "Ochiq osmon ☀️",
        "Mostly sunny": "Asosan quyoshli 🌤️",
        "Partly cloudy": "Qisman bulutli ⛅",
        "Overcast": "Bulutli ☁️",
        "Fog": "Tuman 🌫️",
        "Light drizzle": "Yengil yog‘ingarchilik 🌦️",
        "Moderate drizzle": "Mo‘tadil yog‘ingarchilik 🌦️",
        "Heavy drizzle": "Kuchli yog‘ingarchilik 🌧️",
        "Light rain": "Yengil yomg‘ir 🌦️",
        "Moderate rain": "Mo‘tadil yomg‘ir 🌧️",
        "Heavy rain": "Kuchli yomg‘ir ⛈️",
        "Light snow": "Yengil qor 🌨️",
        "Snow": "Qor 🌨️",
        "Heavy snow": "Kuchli qor ❄️",
        "Light showers": "Yengil yomg‘ir yog‘ishi 🌦️",
        "Rain showers": "Yomg‘ir yog‘ishi 🌧️",
        "Heavy showers": "Kuchli yomg‘ir yog‘ishi ⛈️",
        "Thunderstorm": "Momaqaldiroq ⛈️"
    },

    "uzc": {
        "Clear sky": "Очиқ осмон ☀️",
        "Mostly sunny": "Асосан қуёшли 🌤️",
        "Partly cloudy": "Қисман булутли ⛅",
        "Overcast": "Булутли ☁️",
        "Fog": "Туман 🌫️",
        "Light drizzle": "Ёппаси ёғингарчилик 🌦️",
        "Moderate drizzle": "Мўътадил ёғингарчилик 🌦️",
        "Heavy drizzle": "Кучли ёғингарчилик 🌧️",
        "Light rain": "Ёппаси ёмғир 🌦️",
        "Moderate rain": "Мўътадил ёмғир 🌧️",
        "Heavy rain": "Кучли ёмғир ⛈️",
        "Light snow": "Ёппаси қор 🌨️",
        "Snow": "Қор 🌨️",
        "Heavy snow": "Кучли қор ❄️",
        "Light showers": "Ёппаси ёмғир ёғиши 🌦️",
        "Rain showers": "Ёмғир ёғиши 🌧️",
        "Heavy showers": "Кучли ёғингарчилик ⛈️",
        "Thunderstorm": "Момақалдироқ ⛈️"
    },

    "ru": {
        "Clear sky": "Ясно ☀️",
        "Mostly sunny": "Преимущественно солнечно 🌤️",
        "Partly cloudy": "Переменная облачность ⛅",
        "Overcast": "Пасмурно ☁️",
        "Fog": "Туман 🌫️",
        "Light drizzle": "Легкая морось 🌦️",
        "Moderate drizzle": "Морось 🌦️",
        "Heavy drizzle": "Сильная морось 🌧️",
        "Light rain": "Небольшой дождь 🌦️",
        "Moderate rain": "Дождь 🌧️",
        "Heavy rain": "Сильный дождь ⛈️",
        "Light snow": "Небольшой снег 🌨️",
        "Snow": "Снег 🌨️",
        "Heavy snow": "Сильный снег ❄️",
        "Light showers": "Небольшие ливни 🌦️",
        "Rain showers": "Ливни 🌧️",
        "Heavy showers": "Сильные ливни ⛈️",
        "Thunderstorm": "Гроза ⛈️"
    },

    "en": {
        "Clear sky": "Clear sky ☀️",
        "Mostly sunny": "Mostly sunny 🌤️",
        "Partly cloudy": "Partly cloudy ⛅",
        "Overcast": "Overcast ☁️",
        "Fog": "Fog 🌫️",
        "Light drizzle": "Light drizzle 🌦️",
        "Moderate drizzle": "Moderate drizzle 🌦️",
        "Heavy drizzle": "Heavy drizzle 🌧️",
        "Light rain": "Light rain 🌦️",
        "Moderate rain": "Moderate rain 🌧️",
        "Heavy rain": "Heavy rain ⛈️",
        "Light snow": "Light snow 🌨️",
        "Snow": "Snow 🌨️",
        "Heavy snow": "Heavy snow ❄️",
        "Light showers": "Light showers 🌦️",
        "Rain showers": "Rain showers 🌧️",
        "Heavy showers": "Heavy showers ⛈️",
        "Thunderstorm": "Thunderstorm ⛈️"
    }
}

# ---------------------------------------------------------
# WEATHER CODE → DESCRIPTION KEY
# ---------------------------------------------------------
WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mostly sunny",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Light showers",
    81: "Rain showers",
    82: "Heavy showers",
    95: "Thunderstorm"
}

# ---------------------------------------------------------
# FETCH WEATHER DATA
# ---------------------------------------------------------
def get_weather(lat, lon, days: int):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=weathercode,temperature_2m_max,temperature_2m_min,"
        "precipitation_sum,windspeed_10m_max"
        "&timezone=Asia/Tashkent"
        f"&forecast_days={min(days, 16)}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except:
        return None


# ---------------------------------------------------------
# FORMAT OUTPUT (translated, clean, no zero-rain)
# ---------------------------------------------------------
def render_weather(data, days: int, lang: str):
    d = data["daily"]

    TITLES = {
        "uz": f"<b>{days} kunlik ob-havo:</b>\n\n",
        "uzc": f"<b>{days} кунлик об-ҳаво:</b>\n\n",
        "ru": f"<b>Прогноз на {days} дней:</b>\n\n",
        "en": f"<b>{days}-day forecast:</b>\n\n",
    }

    out = TITLES.get(lang, TITLES["en"])

    for i in range(len(d["time"])):
        date = datetime.strptime(d["time"][i], "%Y-%m-%d").strftime("%d/%m")

        desc_key = WEATHER_CODE_MAP.get(d["weathercode"][i], "Clear sky")
        desc = WEATHER_DESC.get(lang, WEATHER_DESC["en"]).get(desc_key, desc_key)

        tmax = d["temperature_2m_max"][i]
        tmin = d["temperature_2m_min"][i]
        wind = d["windspeed_10m_max"][i]
        rain = d["precipitation_sum"][i]

        out += f"📅 <b>{date}</b>\n"
        out += f"{desc}\n"
        out += f"🌡 +{tmax}° / {tmin}°\n"
        out += f"💨 {wind} km/h\n"

        if rain > 0:
            out += f"🌧 {rain} mm\n"

        out += "\n"

    return out
