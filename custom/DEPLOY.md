# Deploying Fish Speech API to RunPod Serverless

This guide walks you through deploying the Fish Speech API to RunPod's serverless platform.

## Prerequisites

1. RunPod account with credits
2. Docker Hub account (or another container registry)
3. Git installed locally
4. Docker installed locally

## Step 1: Build and Push Docker Image

1. Clone the repository and navigate to it:
```bash
git clone <your-repo-url>
cd fish-speech-api
```

2. Build the Docker image:
```bash
# Replace with your Docker Hub username
export DOCKER_USERNAME=your-username
docker build -t $DOCKER_USERNAME/fish-speech-api:latest .
```

3. Log in to Docker Hub:
```bash
docker login
```

4. Push the image:
```bash
docker push $DOCKER_USERNAME/fish-speech-api:latest
```

## Step 2: Create RunPod Serverless Endpoint

1. Go to RunPod dashboard: https://runpod.io/console/serverless

2. Click "New Endpoint"

3. Configure the endpoint:
   - Name: `fish-speech-api`
   - Docker Image: `your-username/fish-speech-api:latest`
   - GPU Model: Select based on your needs (recommended: RTX 4090 or higher)
   - Min Memory (MB): `8192` (8GB)
   - Max Workers: Based on your needs (start with 2)
   - Idle Timeout: `300` (5 minutes)
   - Worker Timeout: `300` (5 minutes)
   - Container Disk Size: `20` (GB)
   
4. Advanced Configuration:
```json
{
  "env": {
    "API_KEY": "your-secret-api-key",
    "JWT_SECRET": "your-jwt-secret",
    "MODEL_CACHE_SIZE": "2",
    "MODEL_PATH": "/app/models",
    "VOICES_PATH": "/app/voices"
  }
}
```

5. Click "Deploy"

## Step 3: Test the Deployment

1. Get your RunPod API key from the dashboard

2. Test a basic request:
```python
import runpod

# Initialize RunPod
runpod.api_key = "your-runpod-api-key"
endpoint = "your-endpoint-id"  # Found in endpoint URL

# Test request
response = await runpod.run(endpoint, {
    "input": {
        "api_key": "your-api-key",
        "endpoint": "generate_speech",
        "params": {
            "text": "Hello world",
            "reference_audio": "base64_encoded_audio"
        }
    }
})

print(response)
```

## Step 4: Monitor and Scale

1. **Monitor Usage:**
   - Watch GPU utilization
   - Check average response times
   - Monitor error rates

2. **Adjust Settings:**
   - Increase/decrease max workers based on load
   - Adjust memory allocation if needed
   - Modify timeouts based on request patterns

3. **Cost Optimization:**
   - Set appropriate idle timeout
   - Use batch processing for multiple requests
   - Monitor and adjust worker count

## Troubleshooting

### Common Issues

1. **Container Startup Failure:**
   - Check Docker build logs
   - Verify environment variables
   - Check model download process

2. **Out of Memory:**
   - Increase min memory
   - Reduce model cache size
   - Use model quantization

3. **Timeouts:**
   - Increase worker timeout
   - Check request processing time
   - Optimize batch size

### Logs and Monitoring

1. **View Logs:**
   - Check RunPod endpoint logs
   - Monitor container stdout/stderr
   - Review application logs in `/app/logs`

2. **Performance Metrics:**
   - GPU utilization
   - Memory usage
   - Request latency
   - Error rates

## Production Best Practices

1. **Security:**
   - Rotate API keys regularly
   - Use strong JWT secrets
   - Monitor for unusual patterns

2. **Scaling:**
   - Start with 2-3 workers
   - Monitor queue length
   - Adjust based on usage patterns

3. **Cost Management:**
   - Use batch processing
   - Optimize idle timeout
   - Monitor credit usage

4. **Reliability:**
   - Implement retry logic in clients
   - Set up monitoring alerts
   - Regular backup of voice data

## Updating the Deployment

1. Make changes to your code

2. Build and push new Docker image:
```bash
docker build -t $DOCKER_USERNAME/fish-speech-api:latest .
docker push $DOCKER_USERNAME/fish-speech-api:latest
```

3. Update RunPod endpoint:
   - Go to endpoint settings
   - Click "Update Template"
   - Select new image version
   - Click "Update Workers"

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| API_KEY | Yes | - | API key for authentication |
| JWT_SECRET | Yes | - | Secret for JWT tokens |
| MODEL_CACHE_SIZE | No | 2 | Number of models to keep in memory |
| MODEL_PATH | No | /app/models | Path to model files |
| VOICES_PATH | No | /app/voices | Path to voice files |
| RUNPOD_API_KEY | Yes | - | Your RunPod API key |

## Support

For issues with:
- RunPod platform: [RunPod Support](https://runpod.io/support)
- API implementation: [Create Issue](https://github.com/your-repo/issues)
