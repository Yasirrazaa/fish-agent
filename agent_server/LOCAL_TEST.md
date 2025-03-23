# Testing Fish Agent API Locally

This guide will help you test the Fish Agent API on your local machine before deploying to RunPod.

## Prerequisites

1. GPU Requirements:
   - At least 8GB GPU memory (with quantization)
   - 16GB+ recommended
   - NVIDIA GPU with CUDA support

2. Python Requirements:
   - Python version < 3.12 (required for compile mode)
   - CUDA toolkit installed

## Setup Steps

1. Create a virtual environment:
```bash
# Create venv
python -m venv venv

# Activate venv
# On Windows:
.\venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download models:
```bash
# Create checkpoints directory
mkdir -p checkpoints

# Download Fish Agent model
huggingface-cli download fishaudio/fish-agent-v0.1-3b --local-dir checkpoints/fish-agent-v0.1-3b

# Download Fish Speech model
huggingface-cli download fishaudio/fish-speech-1.4 --local-dir checkpoints/fish-speech-1.4
```

4. Prepare test audio (optional, for voice testing):
```bash
# Place a WAV file named test_audio.wav in the agent_server directory
# The audio should be:
# - 10-30 seconds long
# - Clear voice without background noise
# - Mono channel, 16-bit
```

## Running Tests

1. Basic test without voice:
```bash
python test_local.py
```

2. With voice cloning (if you have test_audio.wav):
```bash
# Make sure test_audio.wav exists in the agent_server directory
python test_local.py
```

## Test Cases

1. **Simple Chat:**
   - Tests basic text response
   - No context or voice needed
   - Quick sanity check

2. **Chat with Context:**
   - Tests conversation memory
   - Uses conversation_id
   - Checks context understanding

3. **Chat with Voice (optional):**
   - Tests voice cloning
   - Requires test_audio.wav
   - Generates audio response

## Expected Output

1. Text-only response:
```json
{
    "id": "test-job",
    "status": "success",
    "output": {
        "text": "Hello! I'm doing well, thank you for asking..."
    }
}
```

2. Voice response:
```json
{
    "id": "test-job",
    "status": "success",
    "output": {
        "text": "Here's a short story...",
        "audio": [...] // NumPy array as list
    }
}
```

## Troubleshooting

1. **CUDA/GPU Issues:**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi
```

2. **Model Loading Issues:**
```bash
# Verify model files
ls -l checkpoints/fish-agent-v0.1-3b
ls -l checkpoints/fish-speech-1.4
```

3. **Memory Issues:**
- Monitor GPU memory usage with `nvidia-smi`
- Reduce max_tokens if needed
- Enable quantization in handler.py

4. **Slow First Run:**
- First run includes model compilation
- Be patient, subsequent runs are faster
- Watch GPU utilization

## Performance Tips

1. **GPU Memory:**
```python
# In handler.py
torch.cuda.empty_cache()  # Called automatically after each request
```

2. **Response Speed:**
- Use smaller max_tokens for testing
- Keep reference audio short
- Monitor token generation speed

3. **Audio Testing:**
- Use clear, noise-free audio
- Keep test audio between 10-30 seconds
- Use mono channel WAV format

## Example Test Output

```
Starting local test...
Initializing handler (this might take a while for first run)...

Running test: Simple Chat
Input: {
  "message": "Hello! How are you?",
  "temperature": 0.7,
  "max_tokens": 1000
}
Output: {
  "id": "test-job",
  "status": "success",
  "output": {
    "text": "Hello! I'm doing well, thank you for asking..."
  }
}

Running test: Chat with Context
...

Test completed!
```

## Next Steps

After successful local testing:
1. Build Docker image using Dockerfile
2. Test the Docker container locally
3. Deploy to RunPod following DEPLOY.md
