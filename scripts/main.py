# src/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import time
import threading
import tempfile
from pathlib import Path
import json
import mlx.core as mx
from .whisper_turbo import Transcriber
from huggingface_hub import snapshot_download
import gc
import uvicorn
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Set to ERROR to minimize logging overhead
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhisperTurboAPI",
    description="An optimized FastAPI server for transcribing audio files using the Whisper model with MLX optimization",
    version="1.0.0"
)

# Update cache directory to be relative to project
BASE_DIR = Path(__file__).parent.parent  # Gets the project root directory
CACHE_DIR = BASE_DIR / 'data' / '.whisper_cache'  # Store cache in data directory
UPLOAD_DIR = BASE_DIR / 'data' / 'uploads'  # Make upload path absolute

# Configure CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variables for the model
model = None
model_loaded = threading.Event()

def load_model():
    """
    Load the Whisper model in a background thread.
    """
    global model
    try:
        # Update cache directory
        cache_dir = CACHE_DIR
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Paths for cached weights and config
        cached_weights = cache_dir / 'model.safetensors'
        cached_config = cache_dir / 'config.json'

        # Download model files if not present
        if not cached_weights.exists() or not cached_config.exists():
            path_hf = snapshot_download(
                repo_id='openai/whisper-large-v3-turbo',
                allow_patterns=["config.json", "model.safetensors"],
                cache_dir=cache_dir
            )
            # Copy files to cache directory
            os.system(f'cp {path_hf}/model.safetensors {cached_weights}')
            os.system(f'cp {path_hf}/config.json {cached_config}')

        # Load configuration and weights
        with open(cached_config, 'r') as fp:
            cfg = json.load(fp)
        weights = mx.load(str(cached_weights))
        weights = [
            (
                k.replace("embed_positions.weight", "positional_embedding"),
                v.swapaxes(1, 2) if ('conv' in k and v.ndim == 3) else v
            )
            for k, v in weights.items()
        ]

        # Initialize and load the model
        model_instance = Transcriber(cfg)
        model_instance.load_weights(weights, strict=False)
        model_instance.eval()
        mx.eval(model_instance)
        gc.collect()

        model = model_instance
        model_loaded.set()
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        model_loaded.set()
        raise

# Start model loading in a background thread
threading.Thread(target=load_model).start()

async def transcribe_sync(path_audio: str, quick: bool = True, any_lang: bool = True) -> str:
    """
    Asynchronous wrapper for the model's transcription function.

    Args:
        path_audio (str): Path to the audio file.
        quick (bool): Whether to use quick transcription mode.
        any_lang (bool): Whether to use auto-detect for language (True) or English-only (False).

    Returns:
        str: Transcribed text.
    """
    return await asyncio.to_thread(
        lambda: model(
            path_audio=path_audio,
            any_lang=any_lang,
            quick=quick
        ).strip()
    )

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    quick: bool = True,
    any_lang: bool = True
):
    """
    Endpoint to transcribe audio files.

    Args:
        file (UploadFile): Audio file to transcribe.
        quick (bool, optional): Whether to use quick transcription mode (default is True).
        any_lang (bool, optional): Whether to use auto-detect for language (True) or English-only (False) (default is True).

    Returns:
        dict: Transcription result containing the text, elapsed time, and quick mode status.
    """
    start_time = time.time()

    # Wait for the model to be loaded
    if not model_loaded.is_set():
        await asyncio.to_thread(model_loaded.wait)

    if model is None:
        raise HTTPException(status_code=500, detail="Model failed to load.")

    try:
        # Create uploads directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Read the uploaded file content
        content = await file.read()

        # Write content to a temporary file securely
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Transcribe audio asynchronously
        transcription = await transcribe_sync(tmp_file_path, quick, any_lang)

        elapsed_time = time.time() - start_time

        return {
            "text": transcription,
            "elapsed_time": round(elapsed_time, 2),
            "quick_mode": quick,
            "any_lang": any_lang
        }

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Transcription failed.")
    finally:
        # Clean up temporary file
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except Exception as e:
                logger.error(f"Error removing temporary file: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: Status and version information.
    """
    return {"status": "healthy", "version": "1.0.0"}

def run_server():
    """Entry point for the server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    run_server()
