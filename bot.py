import asyncio
import logging
import re
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command

from config import TELEGRAM_TOKEN, BOT_NAMES, MODELS, MODELS_SMART
from classifier import classify, extract_city
from llm import ask
from search import search, get_weather
from voice import transcribe

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ─── История и состояние пользователей ───────────────────────────────────────
# { user_id: { "category": str, "history": [...], "last_time": float, "smart": bool } }
conversations: dict = {}
CONTEXT_TIMEOUT = 30 * 60
MAX_HISTORY = 10

SMART_CATEGORIES = {"code", "network", "legal"}  # категории с кнопкой smart

def get_data(user_id: int) -> dict:
    if user_id not in conversations:
        conversations[user_id] = {"category": None, "history": [], "last_time": time.time(), "smart": False}
    return conversations[user_id]

def get_history(user_id: int) -> list:
    data = get_data(user_id)
    if time.time() - data["last_time"] > CONTEXT_TIMEOUT:
        data["history"] = []
    return data["history"]

def get_category(user_id: int) -> str | None:
    data = get_data(user_id)
    if time.time() - data["last_time"] > CONTEXT_TIMEOUT:
        return None
    return data.get("category")

def is_smart(user_id: int) -> bool:
    return get_data(user_id).get("smart", False)

def set_smart(user_id: int, value: bool):
    get_data(user_id)["smart"] = value

def save_message(user_id: int, category: str, role: str, content: str):
    data = get_data(user_id)
    data["last_time"] = time.time()
    data["category"] = category
    data["history"].append({"role": role, "content": content})
    if len(data["history"]) > MAX_HISTORY * 2:
        data["history"] = data["history"][-(MAX_HISTORY * 2):]

def reset_history(user_id: int):
    data = get_data(user_id)
    data["history"] = []
    data["category"] = None

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
    "general": "general",
}

def md_to_html(text: str) -> str:
    # 1. Убираем think-блоки Qwen и случайные HTML теги от модели
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"<[^>]+>", lambda m: m.group() if m.group() in
                  ("<b>","</b>","<i>","</i>","<code>","</code>",
                   "<pre>","</pre>") else "", text)

    # 2. Экранируем амперсанды вне тегов
    text = text.replace("&", "&amp;")

    # 3. Блоки кода — обрабатываем первыми чтобы не трогать содержимое
    text = re.sub(
        r"```(\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text, flags=re.DOTALL
    )
    text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)

    # 4. Жирный и курсив
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

    # 5. Заголовки → жирный
    text = re.sub(r"^#{1,3} (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # 6. Ссылки
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

async def send_response(message: Message, text: str, keyboard=None):
    html = md_to_html(text)
    parts = split_long_message(html)
    for i, part in enumerate(parts):
        is_last = (i == len(parts) - 1)
        try:
            await message.reply(
                part,
                parse_mode="HTML",
                reply_markup=keyboard if is_last else None
            )
        except Exception:
            await message.reply(part)

# ─── Клавиатура Smart ─────────────────────────────────────────────────────────

def smart_keyboard(user_id: int, category: str) -> InlineKeyboardMarkup | None:
    """Кнопка переключения модели — только для code/network/legal"""
    if category not in SMART_CATEGORIES:
        return None
    smart = is_smart(user_id)
    label = "⚡ Fast модель" if smart else "💎 Smart модель"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label, callback_data=f"toggle_smart:{category}")
    ]])

# ─── Callbacks ────────────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("toggle_smart:"))
async def handle_toggle_smart(callback: CallbackQuery):
    user_id = callback.from_user.id
    category = callback.data.split(":")[1]

    new_smart = not is_smart(user_id)
    set_smart(user_id, new_smart)

    # Обновляем кнопку
    try:
        await callback.message.edit_reply_markup(
            reply_markup=smart_keyboard(user_id, category)
        )
    except Exception:
        pass

    model = MODELS_SMART.get(category) if new_smart else MODELS.get(category)
    badge = "💎 Smart" if new_smart else "⚡ Fast"
    await callback.answer(f"{badge}: {model}")

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
        "Для сложных вопросов нажми кнопку <b>💎 Smart</b> под ответом.\n"
        "/new — начать новый диалог",
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
        "Задай вопрос текстом или голосовым.\n"
        "Бот определит тему и выберет модель автоматически.\n\n"
        "<b>Кнопка под ответом:</b>\n"
        "💎 Smart — умная модель для сложных вопросов\n"
        "⚡ Fast — вернуться к быстрой\n\n"
        "<b>Команды:</b>\n"
        "/new — сбросить контекст\n\n"
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
        text = transcribe(audio_bytes.read(), "voice.ogg")

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
    smart = is_smart(user_id)
    badge = " 💎" if smart and new_category in SMART_CATEGORIES else ""

    status = await message.reply(f"{emoji} <i>{name}{badge}...</i>", parse_mode="HTML")
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
    response = ask(
        user_text, new_category, search_results,
        history=history, use_smart=smart
    )
    save_message(user_id, new_category, "assistant", response)

    await status.delete()
    keyboard = smart_keyboard(user_id, new_category)
    await send_response(message, f"{emoji} {response}", keyboard=keyboard)


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
