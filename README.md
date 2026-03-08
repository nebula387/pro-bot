# 🤖 Pro Assistant Bot

Telegram-бот с автоматическим выбором AI-модели, памятью контекста, голосовым вводом, поиском и погодой.

## Проекты

```
/pro_bot/        ← этот репозиторий (основной ассистент)
/doc_agent/      ← отдельный агент для работы с документами
```

## ✨ Возможности

| Категория | Что умеет | Модель |
|-----------|-----------|--------|
| 💻 Программирование | Код, отладка, архитектура | Qwen3 235B |
| 🌐 Сети и оборудование | Cisco, MikroTik, VPN, Linux | Qwen3 235B |
| ⚖️ Право | Законы, права, договоры | Gemini 2.5 Pro |
| 🌤 Погода | Температура, ветер, прогноз 3 дня | WeatherAPI |
| 🔍 Поиск и анализ | Новости, события, курсы валют | Tavily + Gemini Flash |
| 🤖 Общие вопросы | Всё остальное | Gemini Flash |

### 🎤 Голосовой ввод
Отправляй голосовые сообщения — бот распознаёт речь через Groq Whisper и отвечает текстом.

### 🧠 Память контекста
- Сохраняется пока тема не меняется
- Автосброс после 30 минут молчания
- `/new` — ручной сброс

### 📝 Форматирование
Markdown от модели конвертируется в HTML — блоки кода, жирный текст, ссылки. Длинные ответы разбиваются на части автоматически.

## 🛠 Стек

- **Python 3.10+**
- **aiogram 3.x** — Telegram Bot framework
- **OpenRouter** — AI модели (Qwen3 235B, Gemini 2.5 Pro, Gemini Flash)
- **Groq Whisper** — распознавание речи (бесплатно)
- **Tavily** — поиск в интернете
- **WeatherAPI** — прогноз погоды

## 🔑 Где получить API ключи

| Сервис | Ссылка | Бесплатный tier |
|--------|--------|-----------------|
| Telegram Bot | [@BotFather](https://t.me/BotFather) | ✅ |
| OpenRouter | [openrouter.ai](https://openrouter.ai) | ✅ Есть бесплатные модели |
| Groq | [console.groq.com](https://console.groq.com) | ✅ Бесплатно |
| Tavily | [tavily.com](https://tavily.com) | ✅ 1000 запросов/мес |
| WeatherAPI | [weatherapi.com](https://weatherapi.com) | ✅ 1M запросов/мес |

## 🚀 Установка локально

```bash
git clone https://github.com/ВАШ_НИК/pro-bot.git
cd pro-bot
pip install -r requirements.txt
cp config.example.py config.py
# заполни config.py своими ключами
python bot.py
```

## 🖥 Деплой на VPS (Ubuntu/Debian)

### 1. Подключись и подготовь сервер
```bash
ssh user@ВАШ_IP
sudo apt update && sudo apt install -y python3 python3-pip git nano
```

### 2. Клонируй и настрой
```bash
cd ~
git clone https://github.com/ВАШ_НИК/pro-bot.git
cd pro-bot
pip3 install -r requirements.txt --break-system-packages
cp config.example.py config.py
nano config.py
```

### 3. Создай systemd сервис
```bash
sudo nano /etc/systemd/system/probot.service
```

```ini
[Unit]
Description=Pro Assistant Telegram Bot
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/pro-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable probot
sudo systemctl start probot
```

### Управление
```bash
sudo systemctl status probot         # статус
sudo journalctl -u probot -f         # логи
sudo systemctl restart probot        # перезапуск
```

### Обновление
```bash
cd ~/pro-bot && git pull
sudo systemctl restart probot
```

## 📁 Структура проекта

```
pro-bot/
├── bot.py              # polling, голос, история, форматирование
├── classifier.py       # определяет тему, извлекает город
├── llm.py              # запросы к моделям через OpenRouter
├── search.py           # Tavily поиск + WeatherAPI погода
├── voice.py            # распознавание речи через Groq Whisper
├── prompts.py          # системные промпты по категориям
├── config.py           # ключи (не коммитить!)
├── config.example.py   # пример конфигурации
├── requirements.txt
└── README.md
```

## 💬 Использование

**Личный чат** — пиши или говори напрямую.

**Групповой чат** — обращайся по имени:
```
бот, какая погода в Алматы?
ассистент, как настроить ospf на cisco?
@имя_бота напиши скрипт для парсинга
```

**Команды:**

| Команда | Действие |
|---------|----------|
| `/start` | Приветствие |
| `/new` | Сбросить контекст |
| `/help` | Справка |

## ⚙️ Настройка

`bot.py`:
```python
CONTEXT_TIMEOUT = 30 * 60  # сброс после 30 мин молчания
MAX_HISTORY = 10            # пар вопрос/ответ в памяти
```

`config.py`:
```python
MODELS = {
    "code":    "qwen/qwen3-235b-a22b",
    "network": "qwen/qwen3-235b-a22b",
    "legal":   "google/gemini-2.5-pro",   # или meta-llama/llama-4-maverick
    "search":  "google/gemini-2.0-flash-001",
    "general": "google/gemini-2.0-flash-001",
}
```

## ⚠️ Важно

`config.py` содержит секретные ключи — **не загружай на GitHub!**

`.gitignore` должен содержать:
```
config.py
```

## 🔮 Планы

- [ ] Агент для работы с документами (отдельный репозиторий)
- [ ] Whitelist пользователей
- [ ] Статистика использования

## 📄 Лицензия

MIT
