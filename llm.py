from openai import OpenAI
from config import OPENROUTER_API_KEY, MODELS, MODELS_SMART
from prompts import SYSTEM_PROMPTS

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

REWRITE_PROMPT = """Ты технический редактор. Переформулируй вопрос чётко и профессионально.
Исправь сленг, опечатки, неточные названия технологий и оборудования.
Сохрани исходный смысл вопроса.
Ответь ТОЛЬКО переформулированным вопросом, без пояснений и кавычек.

Вопрос: {question}"""

def rewrite_query(user_message: str, category: str) -> str:
    """Переформулирует вопрос для технических категорий"""
    if category not in ("code", "network"):
        return user_message
    try:
        response = client.chat.completions.create(
            model=MODELS["general"],
            messages=[{"role": "user", "content": REWRITE_PROMPT.format(question=user_message)}],
            max_tokens=200,
            temperature=0,
        )
        rewritten = response.choices[0].message.content.strip()
        if not rewritten or len(rewritten) > len(user_message) * 3:
            return user_message
        return rewritten
    except Exception:
        return user_message

def ask(user_message: str, category: str, search_results: str = None,
        history: list = None, document: str = None,
        use_smart: bool = False) -> tuple[str, str]:
    """
    Возвращает (ответ, переформулированный_вопрос).
    use_smart=True — использует модель из MODELS_SMART если есть.
    """
    rewritten = rewrite_query(user_message, category)

    # Выбираем модель
    if use_smart and category in MODELS_SMART:
        model = MODELS_SMART[category]
    else:
        model = MODELS.get(category, MODELS["general"])

    system = SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS["general"])

    if document:
        system += (
            f"\n\nПользователь загрузил документ для анализа. "
            f"Отвечай на вопросы строго на основе этого документа. "
            f"Если ответа в документе нет — так и скажи.\n\n"
            f"{document}"
        )

    if search_results:
        system += f"\n\nАктуальные данные из интернета:\n{search_results}"

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": rewritten})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
        )
        return response.choices[0].message.content, rewritten
    except Exception as e:
        return f"⚠️ Ошибка модели ({model}): {e}", rewritten
