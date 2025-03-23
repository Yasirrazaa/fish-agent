from typing import Optional, List
import torch
from pydantic import BaseModel, Field
from fastapi import HTTPException
from utils.logger import logger
from utils.models import ModelManager, InferenceOptimizer
import base64
import io

class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, description="ID to maintain conversation context")
    reference_audio: Optional[str] = Field(None, description="Base64 encoded audio for voice cloning")
    stream: bool = Field(False, description="Stream the response")
    temperature: Optional[float] = Field(0.7, ge=0.1, le=1.0)
    max_tokens: Optional[int] = Field(1000, ge=1, le=2000)

class AgentChat:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.conversations = {}  # Store conversation history

    async def chat(self, params: AgentChatRequest) -> dict:
        """
        Process chat request with optional voice response
        """
        try:
            # Get agent model
            agent_model = self.model_manager.get_model('fish-agent')
            agent_model = InferenceOptimizer.optimize_for_inference(agent_model)

            # Get conversation history
            conversation = self.conversations.get(params.conversation_id, [])

            # Prepare generation config
            config = {
                'max_tokens': params.max_tokens,
                'temperature': params.temperature,
                'stream': params.stream
            }

            # Generate response
            logger.info(f"Generating agent response for: {params.message[:100]}...")

            if params.stream:
                # Return generator for streaming
                return self._stream_response(
                    agent_model,
                    params.message,
                    conversation,
                    params.reference_audio,
                    config
                )
            else:
                # Generate complete response
                response = await agent_model.generate(
                    message=params.message,
                    conversation=conversation,
                    **config
                )

                # Update conversation history
                if params.conversation_id:
                    conversation.extend([
                        {"role": "user", "content": params.message},
                        {"role": "assistant", "content": response}
                    ])
                    self.conversations[params.conversation_id] = conversation[-10:]  # Keep last 10 messages

                # Generate speech if reference audio provided
                if params.reference_audio:
                    speech_model = self.model_manager.get_model('fish-speech')
                    speech_model = InferenceOptimizer.optimize_for_inference(speech_model)

                    try:
                        # Decode reference audio
                        audio_bytes = base64.b64decode(params.reference_audio)
                        
                        # Generate speech
                        audio = await speech_model.generate(
                            text=response,
                            reference_audio=audio_bytes
                        )
                        
                        # Convert to base64
                        audio_io = io.BytesIO()
                        torch.save(audio, audio_io)
                        audio_b64 = base64.b64encode(audio_io.getvalue()).decode()
                        
                        return {
                            "status": "success",
                            "text": response,
                            "audio": audio_b64,
                            "duration": len(audio) / speech_model.sample_rate
                        }
                    
                    except Exception as e:
                        logger.error(f"Error generating speech for response: {str(e)}")
                        # Return text response if speech generation fails
                        return {
                            "status": "partial_success",
                            "text": response,
                            "error": f"Speech generation failed: {str(e)}"
                        }

                return {
                    "status": "success",
                    "text": response
                }

        except Exception as e:
            logger.error(f"Error in agent chat: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Chat processing failed: {str(e)}"
            )

        finally:
            InferenceOptimizer.clear_gpu_cache()

    async def _stream_response(
        self,
        agent_model,
        message: str,
        conversation: List[dict],
        reference_audio: Optional[str],
        config: dict
    ):
        """
        Stream agent responses
        """
        try:
            # Start response generation
            async for token in agent_model.generate_stream(
                message=message,
                conversation=conversation,
                **config
            ):
                yield {
                    "status": "streaming",
                    "token": token
                }

            # Generate speech for complete response if needed
            if reference_audio:
                complete_response = "".join(
                    token["token"] for token in agent_model.get_generated_tokens()
                )
                
                speech_model = self.model_manager.get_model('fish-speech')
                speech_model = InferenceOptimizer.optimize_for_inference(speech_model)

                # Generate and stream audio in chunks
                audio_chunks = await speech_model.generate_stream(
                    text=complete_response,
                    reference_audio=base64.b64decode(reference_audio)
                )

                async for chunk in audio_chunks:
                    audio_bytes = io.BytesIO()
                    torch.save(chunk, audio_bytes)
                    chunk_b64 = base64.b64encode(audio_bytes.getvalue()).decode()
                    
                    yield {
                        "status": "streaming_audio",
                        "audio_chunk": chunk_b64
                    }

            yield {"status": "complete"}

        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield {
                "status": "error",
                "error": str(e)
            }

    async def batch_chat(
        self,
        requests: list[AgentChatRequest],
        batch_size: int = 4
    ) -> list:
        """
        Process multiple chat requests in batches
        """
        results = []
        try:
            # Get models
            agent_model = self.model_manager.get_model('fish-agent')
            agent_model = InferenceOptimizer.optimize_for_inference(agent_model)
            
            # Process in batches
            for i in range(0, len(requests), batch_size):
                batch = requests[i:i + batch_size]
                
                # Prepare batch
                messages = []
                for req in batch:
                    conversation = self.conversations.get(req.conversation_id, [])
                    messages.append({
                        'message': req.message,
                        'conversation': conversation,
                        'temperature': req.temperature,
                        'max_tokens': req.max_tokens
                    })
                
                # Generate responses
                logger.info(f"Processing batch of {len(batch)} chat requests")
                responses = await agent_model.generate_batch(messages)
                
                # Process results
                for req, response in zip(batch, responses):
                    result = {"status": "success", "text": response}
                    
                    # Update conversation history
                    if req.conversation_id:
                        conversation = self.conversations.get(req.conversation_id, [])
                        conversation.extend([
                            {"role": "user", "content": req.message},
                            {"role": "assistant", "content": response}
                        ])
                        self.conversations[req.conversation_id] = conversation[-10:]
                    
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error in batch chat processing: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Batch chat processing failed: {str(e)}"
            )
            
        finally:
            InferenceOptimizer.clear_gpu_cache()
            
        return results
