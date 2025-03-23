FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create checkpoints directory
RUN mkdir -p checkpoints

# Download models
RUN pip install --no-cache-dir huggingface-hub && \
    huggingface-cli download fishaudio/fish-agent-v0.1-3b --local-dir checkpoints/fish-agent-v0.1-3b && \
    huggingface-cli download fishaudio/fish-speech-1.4 --local-dir checkpoints/fish-speech-1.4

# Clone and install fish-speech
RUN git clone https://github.com/fishaudio/fish-speech.git && \
    cd fish-speech && \
    pip install -e .[stable] && \
    pip install cachetools

# Copy RunPod handler
COPY handler.py /app/

# Environment variables
ENV PYTHONPATH=/app/fish-speech
ENV MODEL_PATH=/app/checkpoints

# Start the handler
CMD [ "python", "-u", "handler.py" ]
