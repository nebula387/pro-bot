from openai import OpenAI
from config import OPENROUTER_API_KEY, MODELS, MODELS_SMART
from prompts import SYSTEM_PROMPTS

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def ask(user_message: str, category: str, search_results: str = None,
        history: list = None, document: str = None,
        use_smart: bool = False) -> str:

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
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка модели ({model}): {e}"
