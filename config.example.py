# Скопируй в config.py и заполни своими данными

# Telegram
TELEGRAM_TOKEN = "ВАШ_TELEGRAM_TOKEN"

# API ключи
OPENROUTER_API_KEY = "ВАШ_OPENROUTER_KEY"
GROQ_API_KEY = "ВАШ_GROQ_KEY"
TAVILY_API_KEY = "ВАШ_TAVILY_KEY"
WEATHER_API_KEY = "ВАШ_WEATHERAPI_KEY"  # weatherapi.com

# Модели по задачам (OpenRouter)
MODELS = {
    "code":    "qwen/qwen3-235b-a22b",
    "network": "qwen/qwen3-235b-a22b",
    "legal":   "google/gemini-2.5-pro",
    "search":  "google/gemini-2.0-flash-001",
    "general": "google/gemini-2.0-flash-001",
}

# Модель для классификации и извлечения города
CLASSIFIER_MODEL = "google/gemini-2.0-flash-001"

# Имена бота в групповом чате
BOT_NAMES = ["ассистент", "бот", "помощник"]
