# Fish Speech API

A RunPod serverless API for Fish Speech with voice cloning, speech generation, and agent chat capabilities.

## Features

- 🎯 Text-to-Speech with Voice Cloning
- 🤖 Interactive AI Agent Chat
- 🔄 Batch Processing Support
- 🔐 API Key Authentication
- ⚡ Optimized GPU Performance
- 📊 Request Logging
- 💾 Reusable Voice Profiles

## API Endpoints

### Voice Management

1. **Clone Voice**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "clone_voice",
        "params": {
            "reference_audio": "base64_encoded_audio",
            "name": "Voice Name",
            "description": "Optional description",
            "language": "en"  # Optional language code
        }
    }
})
```

2. **List Voices**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "list_voices"
    }
})
```

3. **Get Voice**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "get_voice",
        "params": {
            "voice_id": "voice_20250320_091234"
        }
    }
})
```

4. **Delete Voice**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "delete_voice",
        "params": {
            "voice_id": "voice_20250320_091234"
        }
    }
})
```

### Speech Generation

1. **Generate Speech**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "generate_speech",
        "params": {
            "text": "Text to convert to speech",
            # Either use reference_audio or speaker_id
            "reference_audio": "base64_encoded_audio",  # For one-time use
            "speaker_id": "voice_20250320_091234",     # For stored voice
            "language": "en",                          # Optional
            "emotion": "happy",                        # Optional: happy/sad/neutral
            "speed": 1.0                              # Optional: 0.5-2.0
        }
    }
})
```

2. **Batch Generate Speech**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "batch_generate_speech",
        "params": {
            "items": [
                {
                    "text": "First text",
                    "speaker_id": "voice_20250320_091234"
                },
                {
                    "text": "Second text",
                    "reference_audio": "base64_encoded_audio"
                }
            ],
            "batch_size": 4  # Optional, default: 4
        }
    }
})
```

### Agent Chat

1. **Chat with Agent**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "agent_chat",
        "params": {
            "message": "Your message to the agent",
            "conversation_id": "unique_id",           # Optional: for context
            "reference_audio": "base64_encoded_audio", # Optional: for voice response
            "stream": True,                          # Optional: for streaming
            "temperature": 0.7,                      # Optional: 0.1-1.0
            "max_tokens": 1000                       # Optional: max response length
        }
    }
})
```

2. **Batch Chat**
```python
response = await runpod.run({
    "input": {
        "api_key": "your-api-key",
        "endpoint": "batch_agent_chat",
        "params": {
            "items": [
                {
                    "message": "First message",
                    "conversation_id": "conv1"
                },
                {
                    "message": "Second message",
                    "conversation_id": "conv2"
                }
            ],
            "batch_size": 4  # Optional, default: 4
        }
    }
})
```

## Response Formats

### Success Response
```python
{
    "id": "job_id",
    "status": "success",
    "output": {
        # Endpoint specific data
        "status": "success",
        ...
    }
}
```

### Error Response
```python
{
    "id": "job_id",
    "status": "error",
    "error": {
        "code": 400,  # HTTP status code
        "detail": "Error message"
    }
}
```

## Environment Variables

```bash
# Required
RUNPOD_API_KEY=your-runpod-api-key
JWT_SECRET=your-jwt-secret
API_KEY=your-api-key

# Optional
MODEL_CACHE_SIZE=2        # Number of models to keep in memory
MODEL_PATH=/app/models    # Path to model files
VOICES_PATH=/app/voices   # Path to voice files
```

## Rate Limits

- Default tier: 10 requests/minute
- Premium tier: 100 requests/minute

## Helper Functions

### Audio Processing
```python
def encode_audio(audio_path: str) -> str:
    """Convert audio file to base64"""
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def save_audio(audio_base64: str, output_path: str):
    """Save base64 audio to file"""
    audio_bytes = base64.b64decode(audio_base64)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
```

### Client Example
```python
import runpod
import base64
import asyncio

class FishSpeechClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_speech(self, text: str, voice_id: str = None, reference_audio: str = None):
        params = {"text": text}
        if voice_id:
            params["speaker_id"] = voice_id
        elif reference_audio:
            params["reference_audio"] = reference_audio
            
        response = await runpod.run({
            "input": {
                "api_key": self.api_key,
                "endpoint": "generate_speech",
                "params": params
            }
        })
        
        if response["status"] == "success":
            return response["output"]
        else:
            raise Exception(response["error"]["detail"])

# Usage
async def main():
    client = FishSpeechClient("your-api-key")
    result = await client.generate_speech(
        "Hello world",
        voice_id="voice_20250320_091234"
    )
    save_audio(result["audio"], "output.wav")

asyncio.run(main())
```

## Best Practices

1. **Voice Cloning**
   - Use 10-30 seconds of clean audio for best results
   - Avoid background noise in reference audio
   - Store commonly used voices using `clone_voice`

2. **Speech Generation**
   - Keep text length reasonable (under 2000 characters)
   - Use batch processing for multiple generations
   - Consider emotion and speed parameters for natural speech

3. **Agent Chat**
   - Use conversation_id to maintain context
   - Enable streaming for real-time responses
   - Adjust temperature based on needed creativity

4. **Error Handling**
   - Always check response status
   - Implement retry logic for network errors
   - Handle rate limits gracefully

## Support

For issues and feature requests, please [create an issue](https://github.com/your-repo/issues).
