import os
import sys
import runpod
import torch
from typing import Dict, Any
from loguru import logger

# Add fish-speech to Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_root)

# Import Fish Speech components
from fish_speech.utils.schema import ServeChatRequest, ServeMessage, ServeTTSRequest
from tools.server.model_manager import ModelManager
from tools.server.agent.generate import generate_responses
from tools.server.inference import inference_wrapper

class RunPodHandler:
    def __init__(self):
        # Initialize model manager with environment variables
        self.model_manager = ModelManager(
            mode=os.getenv("MODE", "agent"),
            device=os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu"),
            half=os.getenv("HALF", "true").lower() == "true",
            compile=os.getenv("COMPILE", "true").lower() == "true",
            asr_enabled=os.getenv("ASR_ENABLED", "false").lower() == "true",
            llama_checkpoint_path=os.getenv("LLAMA_CHECKPOINT_PATH"),
            decoder_checkpoint_path=os.getenv("DECODER_CHECKPOINT_PATH"),
            decoder_config_name=os.getenv("DECODER_CONFIG_NAME", "base"),
        )
        
        # Store conversation history
        self.conversations = {}
        
        # Do a warmup run
        logger.info("Warming up models...")
        self._warmup()
        logger.info("Models ready")

    def _warmup(self):
        """Run a quick warmup to initialize models"""
        try:
            # Test text generation
            request = ServeChatRequest(
                messages=[
                    ServeMessage(role="user", parts=[{"type": "text", "text": "Hello"}])
                ],
                streaming=False,
                num_samples=1,
            )
            
            # Generate using agent
            responses = generate_responses(
                self.model_manager.llama_queue,
                self.model_manager.tokenizer,
                self.model_manager.config,
                request,
                torch.tensor([[0]]).to(self.model_manager.device),  # Empty prompt
                self.model_manager.tokenizer.im_end_id,
                self.model_manager.device
            )
            
            # Run through one response
            for _ in responses:
                break
            
            # Test TTS if needed for voice responses
            tts_request = ServeTTSRequest(
                text="Hello world",
                max_new_tokens=100,
                format="wav"
            )
            for _ in inference_wrapper(tts_request, self.model_manager.tts_inference_engine):
                break
                
        except Exception as e:
            logger.error(f"Warmup failed: {str(e)}")
            raise

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
            reference_audio = input_data.get('reference_audio')  # Optional base64 audio
            temperature = input_data.get('temperature', 0.7)
            max_tokens = input_data.get('max_tokens', 1000)
            stream = input_data.get('stream', False)
            
            # Get conversation history
            conversation = []
            if conversation_id and conversation_id in self.conversations:
                conversation = self.conversations[conversation_id]
            
            # Create chat request
            chat_request = ServeChatRequest(
                messages=[
                    *conversation,
                    ServeMessage(role="user", parts=[{"type": "text", "text": message}])
                ],
                streaming=stream,
                num_samples=1,
                temperature=temperature,
                max_new_tokens=max_tokens
            )
            
            # Generate response
            responses = generate_responses(
                self.model_manager.llama_queue,
                self.model_manager.tokenizer,
                self.model_manager.config,
                chat_request,
                torch.tensor([[0]]).to(self.model_manager.device),  # Empty prompt
                self.model_manager.tokenizer.im_end_id,
                self.model_manager.device
            )
            
            # Process responses
            text_response = ""
            for response in responses:
                if stream:
                    text_response += response.delta.part.text if response.delta and response.delta.part else ""
                else:
                    text_response = response.messages[0].parts[0].text
            
            # Update conversation history
            if conversation_id:
                self.conversations[conversation_id] = [
                    *chat_request.messages,
                    ServeMessage(role="assistant", parts=[{"type": "text", "text": text_response}])
                ][-10:]  # Keep last 10 messages
            
            result = {
                "text": text_response
            }
            
            # Generate speech if reference audio provided
            if reference_audio:
                tts_request = ServeTTSRequest(
                    text=text_response,
                    reference_audio=reference_audio,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    format="wav"
                )
                
                audio = None
                for chunk in inference_wrapper(tts_request, self.model_manager.tts_inference_engine):
                    audio = chunk
                
                if audio:
                    result["audio"] = audio.tolist()
            
            return {
                "id": job_id,
                "status": "success",
                "output": result
            }

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            return {
                "id": job_id,
                "status": "error",
                "error": str(e)
            }
            
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

def main():
    logger.info("Initializing RunPod handler...")
    handler = RunPodHandler()
    
    logger.info("Starting RunPod serverless handler...")
    runpod.serverless.start({
        "handler": handler.handler
    })

if __name__ == "__main__":
    main()
