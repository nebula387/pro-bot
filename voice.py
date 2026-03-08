import os
import tempfile
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def transcribe(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Распознаёт речь через Groq Whisper. Возвращает текст."""
    try:
        # Сохраняем во временный файл — Groq требует файл
        suffix = os.path.splitext(filename)[-1] or ".ogg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",  # быстрый и точный
                file=audio_file,
                language="ru",                   # русский приоритет
                response_format="text"
            )

        os.unlink(tmp_path)  # удаляем временный файл
        return transcription.strip()

    except Exception as e:
        return f"ERROR:{e}"
