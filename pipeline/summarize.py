import os
import logging
import requests
 
logger = logging.getLogger(__name__)
 
SUMMARY_MODE = os.getenv("SUMMARY_MODE", "openai")  # "openai" or "ollama"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
 
# Ollama (local LLM, free alternative)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
 
SUMMARY_LANGUAGE = os.getenv("SUMMARY_LANGUAGE", "ru")  # язык summary
 
SYSTEM_PROMPT = """Ты ассистент для создания кратких итогов встреч.
Проанализируй транскрипцию встречи и создай структурированное резюме на русском языке.
 
Резюме должно включать:
1. 📌 Основные темы обсуждения
2. ✅ Принятые решения
3. 📋 Список задач (кто, что, когда)
4. ❓ Открытые вопросы (если есть)
 
Будь краток и конкретен. Используй маркированные списки."""
 
 
def generate_summary(transcript: str, filename: str = "") -> str:
    """Generate meeting summary from transcript."""
    if not transcript.strip():
        return "Транскрипция пустая — резюме недоступно."
 
    prompt = f"""Транскрипция встречи{f' ({filename})' if filename else ''}:
 
{transcript}
 
Создай краткое резюме встречи."""
 
    if SUMMARY_MODE == "ollama":
        return _summarize_ollama(prompt)
    else:
        return _summarize_openai(prompt)
 
 
def _summarize_openai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set, skipping summary")
        return "Summary недоступен (нет API ключа)."
 
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
 
    except Exception as e:
        logger.error(f"OpenAI summary error: {e}")
        return f"Ошибка генерации резюме: {e}"
 
 
def _summarize_ollama(prompt: str) -> str:
    """Use local Ollama for summary generation."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
                "stream": False,
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
 
    except Exception as e:
        logger.error(f"Ollama summary error: {e}")
        return f"Ошибка генерации резюме (Ollama): {e}"