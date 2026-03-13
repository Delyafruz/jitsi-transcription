import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from transcribe import transcribe_audio
from summarize import generate_summary
from rocketchat import send_to_rocketchat
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
 
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "/recordings")
PROCESSED_DIR = os.getenv("PROCESSED_DIR", "/recordings/processed")
SUPPORTED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".ogg", ".mkv", ".m4a"}
 
 
class RecordingHandler(FileSystemEventHandler):
    def __init__(self):
        self.processing = set()
 
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        if str(path) in self.processing:
            return
        # Wait a bit to ensure file is fully written
        time.sleep(3)
        self.process_file(path)
 
    def process_file(self, path: Path):
        if str(path) in self.processing:
            return
        self.processing.add(str(path))
        logger.info(f"New recording detected: {path.name}")
 
        try:
            # Step 1: Transcribe
            logger.info(f"Transcribing {path.name}...")
            transcript = transcribe_audio(str(path))
            if not transcript:
                logger.error(f"Transcription failed for {path.name}")
                return
 
            logger.info(f"Transcription complete ({len(transcript)} chars)")
 
            # Step 2: Generate summary
            logger.info("Generating summary...")
            summary = generate_summary(transcript, filename=path.name)
 
            # Step 3: Send to Rocket.Chat
            logger.info("Sending to Rocket.Chat...")
            message = format_message(path.name, transcript, summary)
            send_to_rocketchat(message)
 
            # Step 4: Move to processed
            move_to_processed(path)
            logger.info(f"Done processing {path.name}")
 
        except Exception as e:
            logger.error(f"Error processing {path.name}: {e}", exc_info=True)
        finally:
            self.processing.discard(str(path))
 
 
def format_message(filename: str, transcript: str, summary: str) -> str:
    meeting_name = Path(filename).stem
    msg = f"""📋 **Итоги встречи: {meeting_name}**
 
---
**📝 Краткое содержание:**
{summary}
 
---
**🎙️ Полная транскрипция:**
{transcript[:3000]}{"..." if len(transcript) > 3000 else ""}
"""
    return msg
 
 
def move_to_processed(path: Path):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    dest = Path(PROCESSED_DIR) / path.name
    path.rename(dest)
    logger.info(f"Moved {path.name} → processed/")
 
 
def main():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
 
    logger.info(f"Watching directory: {RECORDINGS_DIR}")
 
    event_handler = RecordingHandler()
    observer = Observer()
    observer.schedule(event_handler, RECORDINGS_DIR, recursive=False)
    observer.start()
 
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
 
 
if __name__ == "__main__":
    main()