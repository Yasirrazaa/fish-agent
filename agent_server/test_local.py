import asyncio
import base64
import json
from pathlib import Path

# Mock RunPod job format
def create_mock_job(message, reference_audio=None, conversation_id=None):
    job = {
        "id": "test-job",
        "input": {
            "message": message,
            "conversation_id": conversation_id,
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
    
    if reference_audio:
        # Add reference audio if provided
        with open(reference_audio, 'rb') as f:
            audio_base64 = base64.b64encode(f.read()).decode()
        job["input"]["reference_audio"] = audio_base64
    
    return job

async def test_handler():
    # Import handler
    from handler import RunPodHandler
    
    # Initialize handler
    print("Initializing handler (this might take a while for first run)...")
    handler = RunPodHandler()
    
    # Run tests
    async def run_test(name, job):
        print(f"\nRunning test: {name}")
        print("Input:", json.dumps(job["input"], indent=2))
        result = await handler.handler(job)
        print("Output:", json.dumps(result, indent=2))
        return result

    # Test 1: Simple text chat
    job1 = create_mock_job("Hello! How are you?")
    await run_test("Simple Chat", job1)

    # Test 2: Chat with context
    job2 = create_mock_job(
        "What did I just say to you?",
        conversation_id="test-conv-1"
    )
    await run_test("Chat with Context", job2)

    # Test 3: Chat with voice (if reference audio provided)
    reference_audio = Path("test_audio.wav")  # Update path as needed
    if reference_audio.exists():
        job3 = create_mock_job(
            "Please tell me a short story",
            reference_audio=str(reference_audio)
        )
        result = await run_test("Chat with Voice", job3)
        
        # Save output audio if generated
        if result.get("status") == "success" and "audio" in result.get("output", {}):
            output_path = "test_output.wav"
            audio_data = result["output"]["audio"]
            # Convert list back to numpy array and save
            import numpy as np
            np.save(output_path, np.array(audio_data))
            print(f"Saved output audio to {output_path}")

def main():
    print("Starting local test...")
    asyncio.run(test_handler())
    print("\nTest completed!")

if __name__ == "__main__":
    main()
