from openai import OpenAI
from config import OPENROUTER_API_KEY, CLASSIFIER_MODEL

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

CLASSIFY_PROMPT = """Определи категорию вопроса. Ответь ТОЛЬКО одним словом из списка:
- code      — программирование, код, скрипты, ошибки в коде
- network   — сети, роутеры, коммутаторы, Cisco, MikroTik, IP, VPN, firewall
- legal     — законы, права, юридические вопросы, договоры, штрафы
- weather   — погода, температура, осадки, ветер, прогноз погоды
- search    — новости, актуальные события, курсы валют, что сейчас происходит
- general   — всё остальное

Вопрос: {question}"""

CITY_PROMPT = """Извлеки название города из вопроса о погоде.
Ответь ТОЛЬКО названием города на английском языке (для API).
Если город не указан — ответь: unknown

Вопрос: {question}"""

def classify(text: str) -> str:
    """Возвращает категорию: code / network / legal / weather / search / general"""
    try:
        response = client.chat.completions.create(
            model=CLASSIFIER_MODEL,
            messages=[
                {"role": "user", "content": CLASSIFY_PROMPT.format(question=text)}
            ],
            max_tokens=10,
            temperature=0,
        )
        category = response.choices[0].message.content.strip().lower()
        valid = {"code", "network", "legal", "weather", "search", "general"}
        return category if category in valid else "general"
    except Exception:
        return "general"

def extract_city(text: str) -> str:
    """Извлекает город из вопроса о погоде"""
    try:
        response = client.chat.completions.create(
            model=CLASSIFIER_MODEL,
            messages=[
                {"role": "user", "content": CITY_PROMPT.format(question=text)}
            ],
            max_tokens=20,
            temperature=0,
        )
        city = response.choices[0].message.content.strip()
        return city if city.lower() != "unknown" else "Krasnodar"
    except Exception:
        return "Krasnodar"
