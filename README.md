# Pro Assistant Bot

An intelligent Telegram bot that automatically routes requests to the best AI model based on topic. Built with a custom classifier, context memory, voice input, web search, and weather forecasting.

## Live Demo

➡️ [**pro-bot**](https://t.me/nebula387_pro_bot) — try it now

## How It Works

The bot detects the topic of each message and selects the optimal model automatically:

| Topic | Model | Why |
|-------|-------|-----|
| Programming, networking | Qwen3 235B | Best for technical/code tasks |
| Legal questions | Gemini 2.5 Pro | Strong reasoning |
| Web search & news | Gemini Flash + Tavily | Speed + real-time data |
| General chat | Gemini Flash | Fast and cost-efficient |

(The models are currently free and may vary.)

## Features

- **Smart routing** — custom classifier picks the right model per message
- **Voice input** — speech-to-text via Groq Whisper (free tier)
- **Web search** — real-time answers via Tavily API
- **Weather** — 3-day forecast by city name
- **Context memory** — persists within a topic, auto-resets after 30 min
- **Group chat support** — responds when addressed by name or @mention
- **Long message splitting** — auto-splits Telegram's 4096-char limit

## Tech Stack

- Python 3.10+ / aiogram 3.x
- OpenRouter (Qwen3 235B, Gemini 2.5 Pro, Gemini Flash)
- Groq Whisper — voice recognition
- Tavily — web search
- WeatherAPI — weather data
- VPS + systemd — production deployment

## Project Structure
```
pro-bot/
├── bot.py           # polling, voice, history, message formatting
├── classifier.py    # topic detection and city extraction
├── llm.py           # OpenRouter API calls
├── search.py        # Tavily search + WeatherAPI
├── voice.py         # Groq Whisper integration
├── prompts.py       # system prompts per category
├── config.example.py
└── requirements.txt
```
## Quick Start

```bash
git clone https://github.com/nebula387/pro-bot.git
cd pro-bot
pip install -r requirements.txt
cp config.example.py config.py
# fill in your API keys in config.py
python bot.py
```

All API keys have free tiers — see `config.example.py` for details.

## Related

- [**doc-helper**](https://github.com/nebula387/doc-agent) — AI agent for legal document analysis
