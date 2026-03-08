import requests
from tavily import TavilyClient
from config import TAVILY_API_KEY, WEATHER_API_KEY

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Стрелка показывает КУДА дует ветер (развёрнуто на 180° от источника)
WIND_DIRECTIONS = {
    "N":   ("Север",                "⬇️"),
    "NNE": ("Север-Северо-Восток",  "↙️"),
    "NE":  ("Северо-Восток",        "↙️"),
    "ENE": ("Восток-Северо-Восток", "↙️"),
    "E":   ("Восток",               "⬅️"),
    "ESE": ("Восток-Юго-Восток",    "↖️"),
    "SE":  ("Юго-Восток",           "↖️"),
    "SSE": ("Юг-Юго-Восток",        "↖️"),
    "S":   ("Юг",                   "⬆️"),
    "SSW": ("Юг-Юго-Запад",         "↗️"),
    "SW":  ("Юго-Запад",            "↗️"),
    "WSW": ("Запад-Юго-Запад",      "↗️"),
    "W":   ("Запад",                "➡️"),
    "WNW": ("Запад-Северо-Запад",   "↘️"),
    "NW":  ("Северо-Запад",         "↘️"),
    "NNW": ("Север-Северо-Запад",   "↘️"),
}

def format_wind(wind_dir: str, wind_kph: float) -> str:
    name, arrow = WIND_DIRECTIONS.get(wind_dir, (wind_dir, "➡️"))
    return f"{arrow} {wind_kph/3.6:.2f} м/с"

def get_hour_wind(hours: list, target_hour: int) -> str:
    """Возвращает ветер для указанного часа (6, 12, 18)"""
    for hour in hours:
        if f" {target_hour:02d}:00" in hour["time"]:
            return format_wind(hour["wind_dir"], hour["wind_kph"])
    return "—"

def get_weather(city: str) -> str:
    """Получает погоду через WeatherAPI"""
    try:
        url = "http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "days": 3,
            "lang": "ru",
            "aqi": "no",
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if "error" in data:
            return f"❌ Город не найден: {city}"

        loc = data["location"]
        cur = data["current"]
        forecast = data["forecast"]["forecastday"]

        # Текущая погода
        result = (
            f"🌍 {loc['name']}, {loc['country']}\n"
            f"🕐 Обновлено: {cur['last_updated']}\n\n"
            f"🌡 Сейчас: {cur['temp_c']}°C (ощущается {cur['feelslike_c']}°C)\n"
            f"☁️ {cur['condition']['text']}\n"
            f"💨 Ветер: {format_wind(cur['wind_dir'], cur['wind_kph'])}\n"
            f"💧 Влажность: {cur['humidity']}%\n"
            f"👁 Видимость: {cur['vis_km']} км\n\n"
            f"📅 Прогноз на 3 дня:\n"
        )

        for day in forecast:
            d = day["day"]
            hours = day.get("hour", [])

            morning = get_hour_wind(hours, 6)   # 06:00
            midday  = get_hour_wind(hours, 12)  # 12:00
            evening = get_hour_wind(hours, 18)  # 18:00

            result += (
                f"\n📆 {day['date']}\n"
                f"  🌡 {d['mintemp_c']}°C — {d['maxtemp_c']}°C\n"
                f"  ☁️ {d['condition']['text']}\n"
                f"  🌧 Осадки: {d['daily_chance_of_rain']}%\n"
                f"  💨 Ветер:\n\t    - утро   {morning}\n\t    - день   {midday}\n\t    - вечер {evening}\n"
                            )

        return result

    except Exception as e:
        return f"⚠️ Ошибка получения погоды: {e}"


def search(query: str, max_results: int = 5) -> str:
    """Поиск через Tavily"""
    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )

        output = ""
        if response.get("answer"):
            output += f"📌 Краткий ответ: {response['answer']}\n\n"

        for r in response.get("results", []):
            output += f"• {r['title']}\n{r['content'][:300]}...\n{r['url']}\n\n"

        return output if output else "Ничего не найдено."

    except Exception as e:
        return f"Ошибка поиска: {e}"
