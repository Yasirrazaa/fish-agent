#!/usr/bin/env python3
import os
import runpod
from fastapi import FastAPI, HTTPException, Depends
from typing import Optional, Dict, Any

from utils.logger import setup_logger, log_error
from utils.auth import auth_handler, authenticate_request
from utils.models import ModelManager, BatchProcessor
from api.speech import SpeechGenerator, GenerateSpeechRequest
from api.agent import AgentChat, AgentChatRequest
from api.voice import Voice, VoiceCloneRequest

# Initialize components
app = FastAPI()
logger = setup_logger()
model_manager = ModelManager()
speech_generator = SpeechGenerator(model_manager)
agent_chat = AgentChat(model_manager)
batch_processor = BatchProcessor(model_manager)
voice_manager = Voice(model_manager)

class RunPodHandler:
    def __init__(self):
        self.logger = logger
        self.model_manager = model_manager
        self.speech_generator = speech_generator
        self.agent_chat = agent_chat
        
    async def handler(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main handler for RunPod serverless requests
        """
        try:
            job_id = event.get('id', 'unknown')
            self.logger.info(f"Processing job {job_id}")
            
            # Validate input
            if not event.get('input'):
                raise HTTPException(
                    status_code=400,
                    detail="No input provided"
                )
                
            # Extract parameters
            input_data = event['input']
            api_key = input_data.get('api_key')
            endpoint = input_data.get('endpoint')
            params = input_data.get('params', {})
            
            # Authenticate request
            await authenticate_request(api_key)
            
            # Route request to appropriate handler
            result = await self._route_request(endpoint, params)
            
            self.logger.info(f"Completed job {job_id}")
            return {
                "id": job_id,
                "status": "success",
                "output": result
            }
            
        except HTTPException as e:
            log_error(self.logger, e, job_id)
            return {
                "id": job_id,
                "status": "error",
                "error": {
                    "code": e.status_code,
                    "detail": e.detail
                }
            }
            
        except Exception as e:
            log_error(self.logger, e, job_id)
            return {
                "id": job_id,
                "status": "error",
                "error": {
                    "code": 500,
                    "detail": str(e)
                }
            }
    
    async def _route_request(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to appropriate handler based on endpoint
        """
        if endpoint == "generate_speech":
            request = GenerateSpeechRequest(**params)
            return await self.speech_generator.generate_speech(request)
            
        elif endpoint == "batch_generate_speech":
            requests = [GenerateSpeechRequest(**p) for p in params.get('items', [])]
            return await self.speech_generator.batch_generate_speech(
                requests,
                batch_size=params.get('batch_size', 4)
            )
            
        elif endpoint == "agent_chat":
            request = AgentChatRequest(**params)
            return await self.agent_chat.chat(request)
            
        elif endpoint == "batch_agent_chat":
            requests = [AgentChatRequest(**p) for p in params.get('items', [])]
            return await self.agent_chat.batch_chat(
                requests,
                batch_size=params.get('batch_size', 4)
            )
            
        # Voice management endpoints
        elif endpoint == "clone_voice":
            request = VoiceCloneRequest(**params)
            return await voice_manager.clone_voice(request)
            
        elif endpoint == "list_voices":
            return await voice_manager.list_voices()
            
        elif endpoint == "get_voice":
            voice_id = params.get('voice_id')
            if not voice_id:
                raise HTTPException(status_code=400, detail="voice_id is required")
            return await voice_manager.get_voice(voice_id)
            
        elif endpoint == "delete_voice":
            voice_id = params.get('voice_id')
            if not voice_id:
                raise HTTPException(status_code=400, detail="voice_id is required")
            return await voice_manager.delete_voice(voice_id)
            
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown endpoint: {endpoint}"
            )

def main():
    handler = RunPodHandler()
    runpod.serverless.start({
        "handler": handler.handler
    })

if __name__ == "__main__":
    main()
