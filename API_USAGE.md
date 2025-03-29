# Fish Speech API Documentation

## HTTP API Reference

The Fish Speech API can be called using standard HTTP requests. Here's how to interact with it using any programming language.

## Base URL

```
https://api.runpod.ai/v2/{ENDPOINT_ID}/run
```

Replace `{ENDPOINT_ID}` with your RunPod endpoint ID.

## Authentication

Add your RunPod API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### 1. Chat Endpoint

**Request**

```http
POST /run
Content-Type: application/json

{
    "input": {
        "message": "Hello, how are you?",
        "conversation_id": "optional-conversation-id",
        "temperature": 0.7,
        "max_tokens": 1000,
        "reference_audio": "optional-base64-wav-data"
    }
}
```

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message | string | Yes | Text message to process |
| conversation_id | string | No | ID to maintain conversation context |
| temperature | float | No | Sampling temperature (0.1-1.0, default: 0.7) |
| max_tokens | integer | No | Maximum tokens to generate (default: 1000) |
| reference_audio | string | No | Base64-encoded WAV file for voice cloning |

**Response**

```json
{
    "id": "request-id",
    "status": "success",
    "output": {
        "text": "Generated text response",
        "audio": [/* audio data array if reference_audio provided */]
    }
}
```

### Example Requests

#### 1. Basic Text Chat (cURL)

```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/run \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{
    "input": {
        "message": "Hello, how are you?",
        "temperature": 0.7
    }
}'
```

#### 2. Voice Cloning (Python)

```python
import requests
import base64

# Read audio file
with open("speaker.wav", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode()

# Make request
response = requests.post(
    "https://api.runpod.ai/v2/{ENDPOINT_ID}/run",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_KEY"
    },
    json={
        "input": {
            "message": "Say this in the reference voice",
            "reference_audio": audio_b64,
            "temperature": 0.7
        }
    }
)

# Handle response
result = response.json()
if result["status"] == "success":
    text = result["output"]["text"]
    audio_data = result["output"]["audio"]  # List of float values
```

#### 3. Conversation Context (JavaScript)

```javascript
const convoId = "chat-123";

// First message
const response1 = await fetch('https://api.runpod.ai/v2/{ENDPOINT_ID}/run', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
    },
    body: JSON.stringify({
        input: {
            message: "What's the weather?",
            conversation_id: convoId
        }
    })
});

// Follow-up using same conversation_id
const response2 = await fetch('https://api.runpod.ai/v2/{ENDPOINT_ID}/run', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
    },
    body: JSON.stringify({
        input: {
            message: "And what about tomorrow?",
            conversation_id: convoId
        }
    })
});
```

### Error Handling

The API returns standard HTTP status codes and error messages:

```json
{
    "id": "request-id",
    "status": "error",
    "error": "Error message details"
}
```

Common status codes:
- 200: Success
- 400: Bad request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 500: Server error

### Working with Audio

1. When sending reference audio:
   - Must be WAV format
   - 44.1kHz sample rate
   - Convert to base64 before sending
   - Include in "reference_audio" field

2. When receiving audio:
   - Returns array of float values
   - Values range from -1.0 to 1.0
   - 44.1kHz sample rate
   - Convert to desired format in your application

## Streaming Responses

The API supports streaming responses for real-time text and audio output. To use streaming:

```http
POST /run
Content-Type: application/json

{
    "input": {
        "message": "Your message here",
        "stream": true,
        "temperature": 0.7
    }
}
```

### Streaming Examples

#### Python with httpx

```python
import httpx
import json

async def stream_response():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'https://api.runpod.ai/v2/{ENDPOINT_ID}/run',
            headers={
                'Authorization': 'Bearer YOUR_API_KEY',
                'Content-Type': 'application/json'
            },
            json={
                'input': {
                    'message': 'Hello',
                    'stream': True
                }
            }
        ) as response:
            async for chunk in response.aiter_bytes():
                # Each chunk is a length-prefixed msgpack message
                data = json.loads(chunk.decode())
                if data.get('status') == 'success':
                    if 'text' in data['output']:
                        print(data['output']['text'], end='', flush=True)
                    if 'audio' in data['output']:
                        # Process streaming audio chunks
                        pass
```

#### JavaScript Fetch API

```javascript
const response = await fetch('https://api.runpod.ai/v2/{ENDPOINT_ID}/run', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
    },
    body: JSON.stringify({
        input: {
            message: "Hello",
            stream: true
        }
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const data = JSON.parse(chunk);
    
    if (data.status === 'success') {
        if (data.output.text) {
            process.stdout.write(data.output.text);
        }
        if (data.output.audio) {
            // Handle streaming audio data
        }
    }
}
```

## Rate Limits and Performance

- First request may take longer (model loading)
- Voice cloning requests take additional processing time
- Rate limits depend on your RunPod plan
- Consider request timeouts of at least 30 seconds for non-streaming requests
- For streaming, connection may remain open for the duration of response generation