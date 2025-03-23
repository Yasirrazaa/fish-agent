from typing import Optional
import torch
import base64
import io
import numpy as np
from pydantic import BaseModel, Field
from fastapi import HTTPException
from utils.logger import logger
from utils.models import ModelManager, InferenceOptimizer

class GenerateSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    reference_audio: Optional[str] = Field(None, description="Base64 encoded audio file")
    speaker_id: Optional[str] = Field(None, description="ID of a previously used voice")
    language: Optional[str] = Field(None, description="Source language code")
    emotion: Optional[str] = Field(None, regex="^(happy|sad|neutral)$")
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0)

    @classmethod
    def validate_voice_source(cls, values):
        """
        Validate that either reference_audio or speaker_id is provided
        """
        if not values.get('reference_audio') and not values.get('speaker_id'):
            raise ValueError("Either reference_audio or speaker_id must be provided")
        return values

class SpeechGenerator:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    async def generate_speech(self, params: GenerateSpeechRequest) -> dict:
        """
        Generate speech from text
        """
        try:
            # Get model
            model = self.model_manager.get_model('fish-speech')
            
            # Optimize model
            model = InferenceOptimizer.optimize_for_inference(model)
            
            # Prepare inputs
            input_data = {
                'text': params.text,
                'language': params.language,
                'speed': params.speed
            }
            
            # Handle voice source
            if params.reference_audio:
                try:
                    # Decode base64 audio
                    audio_bytes = base64.b64decode(params.reference_audio)
                    input_data['reference_audio'] = audio_bytes
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid reference audio format: {str(e)}"
                    )
            elif params.speaker_id:
                input_data['speaker_id'] = params.speaker_id
                
            # Add emotion if provided
            if params.emotion:
                input_data['emotion'] = params.emotion
                
            # Generate audio
            logger.info(f"Generating speech for text: {params.text[:100]}...")
            audio = await model.generate(**input_data)
            
            # Convert to bytes
            audio_bytes = io.BytesIO()
            torch.save(audio, audio_bytes)
            audio_b64 = base64.b64encode(audio_bytes.getvalue()).decode()
            
            return {
                "status": "success",
                "audio": audio_b64,
                "duration": len(audio) / model.sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Speech generation failed: {str(e)}"
            )
        
        finally:
            # Cleanup
            InferenceOptimizer.clear_gpu_cache()

    async def batch_generate_speech(
        self, 
        requests: list[GenerateSpeechRequest],
        batch_size: int = 4
    ) -> list:
        """
        Generate speech for multiple requests in batches
        """
        results = []
        try:
            # Get model
            model = self.model_manager.get_model('fish-speech')
            model = InferenceOptimizer.optimize_for_inference(model)
            
            # Process in batches
            for i in range(0, len(requests), batch_size):
                batch = requests[i:i + batch_size]
                
                # Prepare batch inputs
                texts = []
                reference_audios = []
                speaker_ids = []
                
                for req in batch:
                    texts.append(req.text)
                    if req.reference_audio:
                        try:
                            audio_bytes = base64.b64decode(req.reference_audio)
                            reference_audios.append(audio_bytes)
                        except:
                            reference_audios.append(None)
                    else:
                        reference_audios.append(None)
                    speaker_ids.append(req.speaker_id)
                
                # Generate batch
                logger.info(f"Processing batch of {len(batch)} requests")
                audios = await model.generate_batch(
                    texts=texts,
                    reference_audios=reference_audios,
                    speaker_ids=speaker_ids
                )
                
                # Process results
                for req, audio in zip(batch, audios):
                    audio_bytes = io.BytesIO()
                    torch.save(audio, audio_bytes)
                    audio_b64 = base64.b64encode(audio_bytes.getvalue()).decode()
                    
                    results.append({
                        "text": req.text,
                        "audio": audio_b64,
                        "duration": len(audio) / model.sample_rate
                    })
                    
        except Exception as e:
            logger.error(f"Error in batch speech generation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Batch speech generation failed: {str(e)}"
            )
            
        finally:
            InferenceOptimizer.clear_gpu_cache()
            
        return results
