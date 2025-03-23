FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set model path environment variable
ENV MODEL_PATH=/app/models

# Create model directory
RUN mkdir -p /app/models

# Download models during build
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('fishaudio/fish-speech-1.4', local_dir='/app/models/fish-speech-1.4'); \
snapshot_download('fishaudio/fish-agent-v0.1-3b', local_dir='/app/models/fish-agent-v0.1-3b');"

# Set runpod serverless handler
CMD [ "python", "-u", "handler.py" ]
