# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LLAMA_CHECKPOINT_PATH="/app/checkpoints/fish-speech-1.5" \
    DECODER_CHECKPOINT_PATH="/app/checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" \
    DECODER_CONFIG_NAME="base" \
    AGENT_CHECKPOINT_PATH=""

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libopenblas-dev \
    libopenmpi-dev \
    libsndfile1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install tiktoken cachetools

# Copy the entire project
COPY --chown=1000:1000 . /app/

# Create checkpoints directory
RUN mkdir -p /app/checkpoints

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "tools.server.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]