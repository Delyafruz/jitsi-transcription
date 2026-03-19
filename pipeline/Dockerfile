FROM python:3.11-slim
 
WORKDIR /app
 
# Install ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
# Default recordings directory
RUN mkdir -p /recordings/processed
 
CMD ["python", "watcher.py"]
 