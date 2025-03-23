from typing import Dict, Optional
import os
import time
import torch
import torch.nn as nn
from pathlib import Path
from threading import Lock
import numpy as np
from utils.logger import setup_logger

logger = setup_logger()

class ModelManager:
    """
    Manages loading and caching of ML models
    """
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "/app/models")
        self.models: Dict[str, nn.Module] = {}
        self.last_used: Dict[str, float] = {}
        self.locks: Dict[str, Lock] = {}
        self.max_cache_size = int(os.getenv("MODEL_CACHE_SIZE", "2"))
        
    def get_model(self, model_name: str):
        """
        Get a model - loads if not in cache
        """
        if model_name not in self.locks:
            self.locks[model_name] = Lock()
            
        with self.locks[model_name]:
            if model_name not in self.models:
                self._cleanup_cache()
                self.models[model_name] = self._load_model(model_name)
            
            self.last_used[model_name] = time.time()
            return self.models[model_name]
    
    def _load_model(self, model_name: str) -> nn.Module:
        """
        Load a model from disk
        """
        logger.info(f"Loading model: {model_name}")
        try:
            if model_name == "fish-speech":
                return self._load_fish_speech()
            elif model_name == "fish-agent":
                return self._load_fish_agent()
            else:
                raise ValueError(f"Unknown model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            raise

    def _load_fish_speech(self) -> nn.Module:
        """
        Load Fish Speech model
        """
        model_dir = Path(self.model_path) / "fish-speech-1.4"
        if not model_dir.exists():
            raise FileNotFoundError(
                "Fish Speech model not found. Please download it first."
            )
            
        # Import here to avoid loading dependencies unless needed
        from fish_speech.models import FishSpeech
        
        model = FishSpeech(
            checkpoint=str(model_dir),
            device="cuda" if torch.cuda.is_available() else "cpu",
            compile_mode=True
        )
        return model

    def _load_fish_agent(self) -> nn.Module:
        """
        Load Fish Agent model
        """
        model_dir = Path(self.model_path) / "fish-agent-v0.1-3b"
        if not model_dir.exists():
            raise FileNotFoundError(
                "Fish Agent model not found. Please download it first."
            )
            
        # Import here to avoid loading dependencies unless needed
        from fish_speech.models import FishAgent
        
        model = FishAgent(
            checkpoint=str(model_dir),
            device="cuda" if torch.cuda.is_available() else "cpu",
            compile_mode=True
        )
        return model

    def _cleanup_cache(self):
        """
        Remove least recently used models if cache is full
        """
        if len(self.models) >= self.max_cache_size:
            # Find least recently used model
            lru_model = min(self.last_used.items(), key=lambda x: x[1])[0]
            
            # Remove it
            logger.info(f"Removing model from cache: {lru_model}")
            with self.locks[lru_model]:
                del self.models[lru_model]
                del self.last_used[lru_model]
                torch.cuda.empty_cache()

class InferenceOptimizer:
    """
    Optimizes models for inference
    """
    @staticmethod
    def optimize_for_inference(model: nn.Module) -> nn.Module:
        """
        Apply inference optimizations to model
        """
        if torch.cuda.is_available():
            # Use half precision
            model = model.half()
            
            # Enable CUDA optimization
            torch.backends.cudnn.benchmark = True
            
        # Set to eval mode
        model.eval()
        
        return model

    @staticmethod
    def clear_gpu_cache():
        """
        Clear GPU cache
        """
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

class BatchProcessor:
    """
    Handles batch processing of requests
    """
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        
    async def process_batch(self, items: list, batch_size: int = 4):
        """
        Process a batch of items
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_batch_items(batch)
            results.extend(batch_results)
        return results
            
    async def _process_batch_items(self, items: list):
        """
        Process a single batch of items
        """
        results = []
        try:
            # Group by model type
            speech_items = []
            agent_items = []
            
            for item in items:
                if item['type'] == 'generate_speech':
                    speech_items.append(item)
                elif item['type'] == 'agent_chat':
                    agent_items.append(item)
                    
            # Process each group
            if speech_items:
                speech_model = self.model_manager.get_model('fish-speech')
                speech_results = await self._batch_generate_speech(
                    speech_model, 
                    speech_items
                )
                results.extend(speech_results)
                
            if agent_items:
                agent_model = self.model_manager.get_model('fish-agent')
                agent_results = await self._batch_chat(
                    agent_model, 
                    agent_items
                )
                results.extend(agent_results)
                
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            raise
            
        finally:
            InferenceOptimizer.clear_gpu_cache()
            
        return results
    
    async def _batch_generate_speech(self, model, items):
        """
        Generate speech for multiple items
        """
        texts = [item['text'] for item in items]
        try:
            audios = await model.generate_batch(texts)
            return [
                {'id': item['id'], 'audio': audio.tolist()} 
                for item, audio in zip(items, audios)
            ]
        except Exception as e:
            logger.error(f"Error in batch speech generation: {str(e)}")
            raise

    async def _batch_chat(self, model, items):
        """
        Process multiple chat messages
        """
        messages = [item['message'] for item in items]
        try:
            responses = await model.generate_batch(messages)
            return [
                {'id': item['id'], 'response': response} 
                for item, response in zip(items, responses)
            ]
        except Exception as e:
            logger.error(f"Error in batch chat: {str(e)}")
            raise
