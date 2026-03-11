# Скопируй в config.py и заполни своими данными

# Telegram
TELEGRAM_TOKEN = "ВАШ_TELEGRAM_TOKEN"

# API ключи
OPENROUTER_API_KEY = "ВАШ_OPENROUTER_KEY"
GROQ_API_KEY       = "ВАШ_GROQ_KEY"
TAVILY_API_KEY     = "ВАШ_TAVILY_KEY"
WEATHER_API_KEY    = "ВАШ_WEATHERAPI_KEY"

# Модели по умолчанию (бесплатные)
MODELS = {
    "code":    "deepseek/deepseek-v3",
    "network": "deepseek/deepseek-v3",    # сильная бесплатная
    "legal":   "meta-llama/llama-4-maverick",   # сильная бесплатная
    "search":  "google/gemini-2.0-flash-001",
    "general": "google/gemini-2.0-flash-001",
}

# Smart модели по кнопке (платные/мощные)
MODELS_SMART = {
    "code":    "qwen/qwen3-235b-a22b",          # лучший для кода
    "network": "qwen/qwen3-235b-a22b",          # лучший для сетей
    "legal":   "google/gemini-2.5-pro",         # лучший для права
}

# Модель для классификации и переформулирования
CLASSIFIER_MODEL = "google/gemini-2.0-flash-001"

# Имена бота в групповом чате
BOT_NAMES = ["ассистент", "бот", "помощник"]
