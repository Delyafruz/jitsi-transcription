import os
import logging
import requests
 
logger = logging.getLogger(__name__)
 
WHISPER_MODE = os.getenv("WHISPER_MODE", "local")  # "local" or "openai"
 
# Local Whisper (faster-whisper / whisper.cpp via API)
WHISPER_LOCAL_URL = os.getenv("WHISPER_LOCAL_URL", "http://whisper:9000/asr")
 
# OpenAI Whisper API (fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru")  # ru, en, etc.
 
 
def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file using Whisper."""
    if WHISPER_MODE == "openai":
        return _transcribe_openai(file_path)
    else:
        return _transcribe_local(file_path)
 
 
def _transcribe_local(file_path: str) -> str:
    """
    Send audio to local Whisper container (faster-whisper-server or whisper.cpp).
    Compatible with: https://github.com/fedirz/faster-whisper-server
    """
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                WHISPER_LOCAL_URL,
                files={"audio_file": (os.path.basename(file_path), f)},
                params={
                    "task": "transcribe",
                    "language": WHISPER_LANGUAGE,
                    "output": "txt",
                },
                timeout=600,  # 10 min for long recordings
            )
        response.raise_for_status()
 
        # faster-whisper-server returns JSON with "text" field
        data = response.json()
        if isinstance(data, dict):
            return data.get("text", "").strip()
        return str(data).strip()
 
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to local Whisper at {WHISPER_LOCAL_URL}")
        raise
    except Exception as e:
        logger.error(f"Local Whisper error: {e}")
        raise
 
 
def _transcribe_openai(file_path: str) -> str:
    """Fallback: use OpenAI Whisper API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set for OpenAI Whisper mode")
 
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": (os.path.basename(file_path), f)},
                data={
                    "model": "whisper-1",
                    "language": WHISPER_LANGUAGE,
                    "response_format": "text",
                },
                timeout=300,
            )
        response.raise_for_status()
        return response.text.strip()
 
    except Exception as e:
        logger.error(f"OpenAI Whisper error: {e}")
        raise
 