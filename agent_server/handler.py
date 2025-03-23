import os
import runpod
import asyncio
import torch
from typing import Dict, Any

# Import from fish-speech
from tools.api_server import create_app
from tools.server.model_manager import ModelManager
from tools.server.inference import InferenceEngine
from tools.server.agent.generate import AgentGenerator

class RunPodHandler:
    def __init__(self):
        # Initialize model manager
        self.model_manager = ModelManager()
        
        # Initialize inference engine with compile mode
        self.inference_engine = InferenceEngine(
            llama_checkpoint_path=os.path.join(os.getenv("MODEL_PATH"), "fish-agent-v0.1-3b"),
            mode="agent",
            compile=True
        )
        
        # Initialize agent generator
        self.agent_generator = AgentGenerator(self.inference_engine)
        
        # Store conversation history
        self.conversations = {}

    async def handler(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle RunPod serverless requests
        """
        try:
            job_id = job.get('id', 'unknown')
            input_data = job.get('input', {})
            
            if not input_data:
                raise ValueError("No input provided")
            
            # Get request parameters
            message = input_data.get('message')
            if not message:
                raise ValueError("No message provided")
            
            conversation_id = input_data.get('conversation_id')
            reference_audio = input_data.get('reference_audio')
            stream = input_data.get('stream', False)
            temperature = input_data.get('temperature', 0.7)
            max_tokens = input_data.get('max_tokens', 1000)
            
            # Get conversation history
            conversation = self.conversations.get(conversation_id, []) if conversation_id else []
            
            # Generate response
            response = await self.agent_generator.generate(
                message=message,
                conversation=conversation,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Update conversation history
            if conversation_id:
                conversation.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response}
                ])
                self.conversations[conversation_id] = conversation[-10:]  # Keep last 10 messages
            
            # Generate speech if reference audio provided
            if reference_audio:
                audio = await self.inference_engine.generate_speech(
                    text=response,
                    reference_audio=reference_audio
                )
                
                return {
                    "id": job_id,
                    "status": "success",
                    "output": {
                        "text": response,
                        "audio": audio.tolist()
                    }
                }
            
            return {
                "id": job_id,
                "status": "success",
                "output": {
                    "text": response
                }
            }

        except Exception as e:
            return {
                "id": job_id,
                "status": "error",
                "error": str(e)
            }
        
        finally:
            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    async def healthcheck(self) -> bool:
        """
        Check if models are loaded and working
        """
        try:
            # Simple test generation
            response = await self.agent_generator.generate(
                message="Hello",
                max_tokens=10
            )
            return True
        except:
            return False

def main():
    handler = RunPodHandler()
    
    # Run a health check
    asyncio.run(handler.healthcheck())
    
    # Start the serverless handler
    runpod.serverless.start({
        "handler": handler.handler
    })

if __name__ == "__main__":
    main()
