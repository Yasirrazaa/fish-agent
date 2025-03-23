# Fish Agent API Deployment Guide

This guide explains how to deploy the Fish Agent API to RunPod serverless.

## Requirements

- RunPod account with GPU credits
- Docker Hub account
- Git installation
- 16GB+ GPU (RTX 4090 recommended for best performance)

## Directory Structure

```
agent_server/
├── Dockerfile         # Container configuration
├── handler.py         # RunPod serverless handler
├── requirements.txt   # Python dependencies
└── DEPLOY.md         # This guide
```

## Step 1: Build and Push Docker Image

1. Clone the repository and navigate to the agent_server directory:
```bash
cd agent_server
```

2. Build the Docker image:
```bash
export DOCKER_USERNAME=your-username
docker build -t $DOCKER_USERNAME/fish-agent-api:latest .
```

3. Push to Docker Hub:
```bash
docker login
docker push $DOCKER_USERNAME/fish-agent-api:latest
```

## Step 2: Create RunPod Endpoint

1. Go to [RunPod Serverless Console](https://runpod.io/console/serverless)

2. Click "New Endpoint"

3. Configure the endpoint:
   - Name: `fish-agent-api`
   - Docker Image: `your-username/fish-agent-api:latest`
   - GPU Type: RTX 4090 (recommended)
   - Min Memory (MB): `16384` (16GB)
   - Max Workers: `2` (adjust based on needs)
   - Idle Timeout: `300` (5 minutes)
   - Worker Timeout: `300` (5 minutes)
   - Container Disk Size: `20` (GB)

4. Click "Deploy"

## Step 3: Test the API

1. Using Python:
```python
import runpod

# Initialize RunPod
runpod.api_key = "your-runpod-api-key"
endpoint = "your-endpoint-id"

# Test chat without voice
response = await runpod.run(endpoint, {
    "input": {
        "message": "Hello, how are you?",
        "conversation_id": "test-1",  # Optional: for context
        "temperature": 0.7,           # Optional: 0.1-1.0
        "max_tokens": 1000            # Optional: response length
    }
})

print(response)

# Test chat with voice response
response = await runpod.run(endpoint, {
    "input": {
        "message": "Tell me a story",
        "reference_audio": "base64_encoded_audio",  # For voice response
        "conversation_id": "test-2",
        "stream": False,               # Optional: for streaming
        "temperature": 0.7,
        "max_tokens": 1000
    }
})

print(response)
```

2. Expected Response Format:
```python
# Text-only response
{
    "id": "job-id",
    "status": "success",
    "output": {
        "text": "Agent's response text"
    }
}

# Response with voice
{
    "id": "job-id",
    "status": "success",
    "output": {
        "text": "Agent's response text",
        "audio": [audio_array]  # NumPy array converted to list
    }
}
```

## Performance Notes

1. **First Request:**
   - Initial request will be slower due to model compilation
   - Subsequent requests will be faster

2. **Expected Performance:**
   - RTX 4090: ~95 tokens/second
   - RTX 4060: ~8 tokens/second

3. **Memory Usage:**
   - Base memory: ~8GB
   - Peak memory: ~14GB
   - Recommended: 16GB+

## Optimization Tips

1. **GPU Memory:**
   - Models are automatically quantized
   - GPU cache is cleared after each request
   - Only one model is loaded at a time

2. **Response Speed:**
   - Use `stream=False` for faster responses
   - Keep `max_tokens` reasonable
   - Reuse `conversation_id` for context

3. **Cost Optimization:**
   - Adjust idle timeout based on usage
   - Use batch processing when possible
   - Monitor GPU utilization

## Troubleshooting

1. **Container Fails to Start:**
   - Check Docker build logs
   - Verify GPU memory availability
   - Ensure model downloads completed

2. **Slow Responses:**
   - Verify GPU type
   - Check if compilation completed
   - Monitor GPU utilization

3. **Memory Issues:**
   - Increase min memory
   - Reduce max_tokens
   - Clear conversation history regularly

## Environment Variables

No additional environment variables are required, but you can set:
```bash
MODEL_PATH=/app/checkpoints  # Default model path
```

## Monitoring

1. **RunPod Dashboard:**
   - Monitor GPU utilization
   - Check worker status
   - View request logs

2. **Application Logs:**
   - Container logs show compilation status
   - Error messages are detailed
   - Health checks are logged

## Support

- For RunPod issues: [RunPod Support](https://runpod.io/support)
- For Fish Agent issues: [Fish Speech GitHub](https://github.com/fishaudio/fish-speech/issues)
