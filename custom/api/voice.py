from typing import Optional
import torch
import base64
import io
import os
import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import HTTPException
from utils.logger import logger
from utils.models import ModelManager, InferenceOptimizer

class VoiceCloneRequest(BaseModel):
    reference_audio: str = Field(..., description="Base64 encoded audio file (10-30 seconds)")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field(None, description="Primary language of the voice")

class Voice:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.voices_dir = Path(os.getenv("VOICES_PATH", "/app/voices"))
        self.voices_dir.mkdir(exist_ok=True)
        self.voices = self._load_voices()
        
    def _load_voices(self):
        """
        Load existing voice metadata
        """
        voices = {}
        for file in self.voices_dir.glob("*.json"):
            try:
                with open(file) as f:
                    voice_data = json.load(f)
                    voices[voice_data["id"]] = voice_data
            except Exception as e:
                logger.error(f"Error loading voice {file}: {str(e)}")
        return voices

    async def clone_voice(self, params: VoiceCloneRequest) -> dict:
        """
        Create a reusable voice profile from reference audio
        """
        try:
            # Get model
            model = self.model_manager.get_model('fish-speech')
            model = InferenceOptimizer.optimize_for_inference(model)
            
            # Decode reference audio
            try:
                audio_bytes = base64.b64decode(params.reference_audio)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid reference audio format: {str(e)}"
                )
            
            # Extract voice embeddings
            logger.info(f"Extracting voice embeddings for: {params.name}")
            embeddings = await model.extract_voice_embeddings(audio_bytes)
            
            # Generate unique ID
            voice_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Save voice embeddings
            embedding_path = self.voices_dir / f"{voice_id}.pt"
            torch.save(embeddings, embedding_path)
            
            # Save metadata
            voice_data = {
                "id": voice_id,
                "name": params.name,
                "description": params.description,
                "language": params.language,
                "created_at": datetime.now().isoformat(),
                "embedding_path": str(embedding_path)
            }
            
            metadata_path = self.voices_dir / f"{voice_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(voice_data, f, indent=2)
                
            # Add to cache
            self.voices[voice_id] = voice_data
            
            return {
                "status": "success",
                "voice_id": voice_id,
                "name": params.name,
                "message": "Voice cloned successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cloning voice: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Voice cloning failed: {str(e)}"
            )
            
        finally:
            InferenceOptimizer.clear_gpu_cache()

    async def get_voice(self, voice_id: str) -> dict:
        """
        Get voice profile data
        """
        if voice_id not in self.voices:
            raise HTTPException(
                status_code=404,
                detail=f"Voice not found: {voice_id}"
            )
            
        return self.voices[voice_id]

    async def list_voices(self) -> list:
        """
        List all available voices
        """
        return list(self.voices.values())

    async def delete_voice(self, voice_id: str) -> dict:
        """
        Delete a voice profile
        """
        if voice_id not in self.voices:
            raise HTTPException(
                status_code=404,
                detail=f"Voice not found: {voice_id}"
            )
            
        try:
            voice_data = self.voices[voice_id]
            
            # Delete files
            embedding_path = Path(voice_data["embedding_path"])
            if embedding_path.exists():
                embedding_path.unlink()
                
            metadata_path = self.voices_dir / f"{voice_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()
                
            # Remove from cache
            del self.voices[voice_id]
            
            return {
                "status": "success",
                "message": f"Voice {voice_id} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting voice {voice_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting voice: {str(e)}"
            )

    def get_voice_embeddings(self, voice_id: str) -> torch.Tensor:
        """
        Get voice embeddings for generation
        """
        if voice_id not in self.voices:
            raise HTTPException(
                status_code=404,
                detail=f"Voice not found: {voice_id}"
            )
            
        try:
            voice_data = self.voices[voice_id]
            embedding_path = Path(voice_data["embedding_path"])
            
            if not embedding_path.exists():
                raise FileNotFoundError(f"Voice embeddings file not found: {embedding_path}")
                
            return torch.load(embedding_path)
            
        except Exception as e:
            logger.error(f"Error loading voice embeddings for {voice_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error loading voice embeddings: {str(e)}"
            )
