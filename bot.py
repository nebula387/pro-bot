import asyncio
import logging
import re
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from config import TELEGRAM_TOKEN, BOT_NAMES
from classifier import classify, extract_city
from llm import ask
from search import search, get_weather
from voice import transcribe

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ─── История диалогов ─────────────────────────────────────────────────────────
conversations: dict = {}
CONTEXT_TIMEOUT = 30 * 60
MAX_HISTORY = 10

def get_history(user_id: int) -> list:
    data = conversations.get(user_id)
    if not data:
        return []
    if time.time() - data["last_time"] > CONTEXT_TIMEOUT:
        conversations.pop(user_id, None)
        return []
    return data["history"]

def get_category(user_id: int) -> str | None:
    data = conversations.get(user_id)
    if not data:
        return None
    if time.time() - data["last_time"] > CONTEXT_TIMEOUT:
        return None
    return data.get("category")

def save_message(user_id: int, category: str, role: str, content: str):
    if user_id not in conversations:
        conversations[user_id] = {"category": category, "history": [], "last_time": time.time()}
    data = conversations[user_id]
    data["last_time"] = time.time()
    data["category"] = category
    data["history"].append({"role": role, "content": content})
    if len(data["history"]) > MAX_HISTORY * 2:
        data["history"] = data["history"][-(MAX_HISTORY * 2):]

def reset_history(user_id: int):
    conversations.pop(user_id, None)

# ─── Форматирование ───────────────────────────────────────────────────────────

CATEGORY_EMOJI = {
    "code":    "💻",
    "network": "🌐",
    "legal":   "⚖️",
    "weather": "🌤",
    "search":  "🔍",
    "general": "🤖",
}

CATEGORY_NAME = {
    "code":    "Программирование",
    "network": "Сети и оборудование",
    "legal":   "Право",
    "weather": "Погода",
    "search":  "Поиск и анализ",
    "general": "Общий вопрос",
}

def md_to_html(text: str) -> str:
    # Убираем блоки размышлений Qwen
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    text = text.replace("&", "&amp;")
    # ... остальной код без изменений

# def md_to_html(text: str) -> str:
#     text = text.replace("&", "&amp;")
    text = re.sub(
        r"```(\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text, flags=re.DOTALL
    )
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    text = re.sub(r"^#{1,3} (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text.strip()

def split_long_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    parts.append(text)
    return parts

async def send_response(message: Message, text: str):
    html = md_to_html(text)
    for part in split_long_message(html):
        try:
            await message.reply(part, parse_mode="HTML")
        except Exception:
            await message.reply(part)

# ─── Команды ─────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def start(message: Message):
    await message.reply(
        "👋 Привет! Я профессиональный ассистент.\n\n"
        "Помогу с:\n"
        "💻 Программированием и кодом\n"
        "🌐 Настройкой сетей и оборудования\n"
        "⚖️ Юридическими вопросами\n"
        "🌤 Погодой и прогнозом\n"
        "🔍 Актуальными новостями и поиском\n\n"
        "Пиши текстом или отправляй голосовые!\n"
        "/new — начать новый диалог\n"
        "/help — справка",
        parse_mode="HTML"
    )

@dp.message(Command("new"))
async def new_dialog(message: Message):
    reset_history(message.from_user.id)
    await message.reply("🔄 Начат новый диалог!")

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.reply(
        "ℹ️ <b>Как пользоваться:</b>\n\n"
        "Задай вопрос текстом или голосовым сообщением.\n"
        "Бот определит тему и выберет лучшую модель.\n"
        "Контекст диалога сохраняется пока тема не меняется.\n\n"
        "<b>Команды:</b>\n"
        "/new — сбросить контекст, начать заново\n\n"
        "<b>Примеры:</b>\n"
        "• <i>Какая погода в Москве?</i>\n"
        "• <i>Как настроить VLAN на Cisco?</i>\n"
        "• <i>Напиши скрипт на Python</i>\n"
        "• <i>Какие права у работника при увольнении?</i>\n\n"
        "В групповом чате: <b>бот, вопрос</b>",
        parse_mode="HTML"
    )

# ─── Голосовые сообщения ──────────────────────────────────────────────────────

@dp.message(F.voice)
async def handle_voice(message: Message):
    status = await message.reply("🎤 <i>Распознаю речь...</i>", parse_mode="HTML")

    try:
        file = await bot.get_file(message.voice.file_id)
        audio_bytes = await bot.download_file(file.file_path)
        content = audio_bytes.read()

        text = transcribe(content, "voice.ogg")

        if text.startswith("ERROR:") or not text:
            await status.delete()
            await message.reply("❌ Не удалось распознать речь. Попробуй ещё раз.")
            return

        await status.edit_text(f"🎤 <i>Распознано:</i> {text}", parse_mode="HTML")
        await process_message(message, text)

    except Exception as e:
        await status.delete()
        await message.reply(f"❌ Ошибка обработки голоса: {e}")

# ─── Основная логика ──────────────────────────────────────────────────────────

async def process_message(message: Message, user_text: str):
    user_id = message.from_user.id
    new_category = classify(user_text)
    prev_category = get_category(user_id)
    history = get_history(user_id)

    if prev_category and prev_category != new_category:
        reset_history(user_id)
        history = []
        await message.reply(
            f"🔄 <i>Переключаюсь на {CATEGORY_NAME.get(new_category, new_category)}...</i>",
            parse_mode="HTML"
        )

    emoji = CATEGORY_EMOJI.get(new_category, "🤖")
    name = CATEGORY_NAME.get(new_category, "")
    status = await message.reply(f"{emoji} <i>{name}...</i>", parse_mode="HTML")
    await bot.send_chat_action(message.chat.id, "typing")

    if new_category == "weather":
        city = extract_city(user_text)
        await status.edit_text(f"🌤 <i>Получаю погоду для {city}...</i>", parse_mode="HTML")
        weather_text = get_weather(city)
        await status.delete()
        await message.reply(weather_text)
        return

    search_results = None
    if new_category == "search":
        await status.edit_text("🔍 <i>Ищу актуальную информацию...</i>", parse_mode="HTML")
        search_results = search(user_text)

    save_message(user_id, new_category, "user", user_text)
    response = ask(user_text, new_category, search_results, history=history)
    save_message(user_id, new_category, "assistant", response)

    await status.delete()
    await send_response(message, f"{emoji} {response}")


@dp.message(F.text)
async def handle_message(message: Message):
    user_text = message.text or ""

    if message.chat.type in ["group", "supergroup"]:
        bot_info = await bot.get_me()
        text_lower = user_text.lower()
        is_reply_to_bot = (
            message.reply_to_message and
            message.reply_to_message.from_user.id == bot_info.id
        )
        is_mentioned = f"@{bot_info.username}".lower() in text_lower
        is_called_by_name = any(name in text_lower for name in BOT_NAMES)

        if not is_reply_to_bot and not is_mentioned and not is_called_by_name:
            return

        for name in BOT_NAMES:
            user_text = user_text.replace(name, "").strip()
        user_text = user_text.replace(f"@{bot_info.username}", "").strip()

    if not user_text:
        await message.reply("Напиши свой вопрос 🙂")
        return

    await process_message(message, user_text)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
