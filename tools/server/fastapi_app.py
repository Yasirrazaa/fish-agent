from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import ormsgpack
import numpy as np
import soundfile as sf
import io
import torch
from typing import Annotated
from pydantic import BaseModel
from loguru import logger
import os
import time
import threading

from fish_speech.utils.schema import (
    ServeASRRequest,
    ServeASRResponse,
    ServeChatRequest,
    ServeTTSRequest,
    ServeVQGANDecodeRequest,
    ServeVQGANDecodeResponse,
    ServeVQGANEncodeRequest,
    ServeVQGANEncodeResponse,
)
from tools.server.agent import get_response_generator
from tools.server.api_utils import buffer_to_async_generator, get_content_type, inference_async
from tools.server.inference import inference_wrapper as inference
from tools.server.model_manager import ModelManager
from tools.server.model_utils import (
    batch_asr,
    batch_vqgan_decode,
    cached_vqgan_batch_encode,
)

def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

app = FastAPI()

# Initialize model manager
try:
    model_manager = ModelManager(
        mode=os.getenv("MODE", "tts"),
        device="cuda" if torch.cuda.is_available() else "cpu",
        half=os.getenv("HALF", "true").lower() == "true",
        compile=os.getenv("COMPILE", "true").lower() == "true",
        asr_enabled=os.getenv("ASR_ENABLED", "true").lower() == "true",
        llama_checkpoint_path=get_required_env("LLAMA_CHECKPOINT_PATH"),
        decoder_checkpoint_path=get_required_env("DECODER_CHECKPOINT_PATH"),
        decoder_config_name=get_required_env("DECODER_CONFIG_NAME"),
    )
    model_manager.lock = threading.Lock()
except ValueError as e:
    logger.error(f"Failed to initialize model manager: {str(e)}")
    raise

@app.on_event("startup")
async def startup_event():
    app.state.model_manager = model_manager

@app.get("/v1/health")
async def health_check():
    return {"status": "ok"}

@app.post("/v1/vqgan/encode")
async def vqgan_encode(req: ServeVQGANEncodeRequest):
    decoder_model = app.state.model_manager.decoder_model
    
    start_time = time.time()
    tokens = cached_vqgan_batch_encode(decoder_model, req.audios)
    logger.info(f"[EXEC] VQGAN encode time: {(time.time() - start_time) * 1000:.2f}ms")
    
    return ServeVQGANEncodeResponse(tokens=[i.tolist() for i in tokens])

@app.post("/v1/vqgan/decode")
async def vqgan_decode(req: ServeVQGANDecodeRequest):
    decoder_model = app.state.model_manager.decoder_model
    
    tokens = [torch.tensor(token, dtype=torch.int) for token in req.tokens]
    start_time = time.time()
    audios = batch_vqgan_decode(decoder_model, tokens)
    logger.info(f"[EXEC] VQGAN decode time: {(time.time() - start_time) * 1000:.2f}ms")
    audios = [audio.astype(np.float16).tobytes() for audio in audios]
    
    return ServeVQGANDecodeResponse(audios=audios)

@app.post("/v1/asr")
async def asr(req: ServeASRRequest):
    model_manager = app.state.model_manager
    asr_model = model_manager.asr_model
    lock = model_manager.lock
    
    start_time = time.time()
    audios = [np.frombuffer(audio, dtype=np.float16) for audio in req.audios]
    audios = [torch.from_numpy(audio).float() for audio in audios]
    
    if any(audios.shape[-1] >= 30 * req.sample_rate for audios in audios):
        raise HTTPException(status_code=400, detail="Audio length is too long")
    
    transcriptions = batch_asr(
        asr_model, lock, audios=audios, sr=req.sample_rate, language=req.language
    )
    logger.info(f"[EXEC] ASR time: {(time.time() - start_time) * 1000:.2f}ms")
    
    return ServeASRResponse(transcriptions=transcriptions)

@app.post("/v1/tts")
async def tts(req: ServeTTSRequest):
    model_manager = app.state.model_manager
    engine = model_manager.tts_inference_engine
    sample_rate = engine.decoder_model.spec_transform.sample_rate
    
    if req.streaming:
        return StreamingResponse(
            inference_async(req, engine),
            media_type=get_content_type(req.format),
            headers={
                "Content-Disposition": f"attachment; filename=audio.{req.format}",
            }
        )
    else:
        fake_audios = next(inference(req, engine))
        buffer = io.BytesIO()
        sf.write(buffer, fake_audios, sample_rate, format=req.format)
        
        return StreamingResponse(
            buffer_to_async_generator(buffer.getvalue()),
            media_type=get_content_type(req.format),
            headers={
                "Content-Disposition": f"attachment; filename=audio.{req.format}",
            }
        )

@app.post("/v1/chat")
async def chat(request: Request, req: ServeChatRequest):
    model_manager = app.state.model_manager
    llama_queue = model_manager.llama_queue
    tokenizer = model_manager.tokenizer
    config = model_manager.config
    
    response_generator = get_response_generator(
        llama_queue,
        tokenizer,
        config,
        req,
        model_manager.device,
        json_mode="application/json" in request.headers.get("Content-Type", "")
    )
    
    if req.streaming:
        return StreamingResponse(
            response_generator(),
            media_type="text/event-stream"
        )
    else:
        result = response_generator()
        return JSONResponse(result.dict())