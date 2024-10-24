# WhisperTurboAPI

An optimized FastAPI server implementation of OpenAI's Whisper large-v3-turbo model using MLX optimization, designed for low-latency, asynchronous and synchronous audio transcription on macOS.

## Features

- 🎙️ **Fast Audio Transcription:** Leverage the turbocharged, MLX-optimized Whisper large-v3-turbo model for quick and accurate transcriptions.
- 🌐 **RESTful API Access:** Easily integrate with any environment that supports HTTP requests.
- ⚡ **Async/Sync Support:** Seamlessly handle both asynchronous and synchronous transcription requests.
- 🔄 **Low Latency:** Optimized for minimal delay by preloading models and efficient processing.
- 🔧 **High Throughput:** Capable of handling multiple concurrent transcription requests.
- 🚀 **Easy Setup:** Simple setup process.

## System Requirements

- **Operating System:** macOS with Apple Silicon (recommended for optimal performance due to MLX optimizations)
- **Python Version:** 3.12.3 (required for MLX optimization)
- **Python Version Manager:** [pyenv](https://github.com/pyenv/pyenv) (recommended but optional)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kristofferv98/whisper_turboapi.git
cd whisper_turboapi
```

### 2. Run the Setup Script

The `setup.sh` script will handle the environment setup, including checking for the required Python version, creating a virtual environment, installing dependencies, and verifying the installation.

```bash
./setup.sh
```

Optional Flags:

- `-y` or `--yes`: Run in headless mode (assume 'yes' to all prompts)
- `-p` or `--python-version`: Specify the required Python version (default: 3.12.3)
- `-f` or `--force`: Force actions like recreating the virtual environment
- `-h` or `--help`: Display help message

Example:

```bash
./setup.sh -y
```

This will run the setup in headless mode, assuming 'yes' to all prompts.

### 3. Start the Server

After the setup completes, you can start the server using:

```bash
./start_server.sh
```

The server supports several command-line options:

```bash
./start_server.sh --host=0.0.0.0  # Custom host (default: 0.0.0.0)
./start_server.sh --port=8080     # Custom port (default: 8000)
./start_server.sh --help          # Show help message
```

You can combine options:
```bash
./start_server.sh --host=127.0.0.1 --port=8080
```

The server will automatically:
- Activate the virtual environment if not already active
- Verify all required packages are installed
- Start the FastAPI server with the specified host and port

**Note**: The `start_server.sh` script ensures that the virtual environment is activated and that all required packages are installed before starting the server.

## Usage Examples

### Simple Python Client

Here’s a basic synchronous client example using `requests`.

```python
import requests
import os

def transcribe_audio(file_path, quick=True, any_lang=True, server_url="http://localhost:8000"):
    """
    Simplified function to transcribe an audio file using the WhisperTurboAPI server.

    Args:
        file_path (str): Path to the audio file.
        quick (bool, optional): Whether to use quick mode. Default is True.
        any_lang (bool, optional): Whether to allow any language detection. Default is True.
        server_url (str, optional): URL of the transcription server.

    Returns:
        str: The transcribed text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
        
    if not file_path.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
        raise ValueError("Unsupported audio format. Use WAV, MP3, M4A, or FLAC")
        
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'audio/wav')}
        params = {
            'quick': str(quick).lower(),
            'any_lang': str(any_lang).lower()
        }
        response = requests.post(f"{server_url}/transcribe", files=files, params=params)
    if response.status_code == 200:
        return response.json()['text']
    else:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

# Example usage
if __name__ == "__main__":
    # Replace 'path/to/audio.wav' with the path to your audio file
    audio_file = 'path/to/audio.wav'
    try:
        transcription = transcribe_audio(audio_file, quick=True, any_lang=False)
        print("Transcription:")
        print(transcription)
    except Exception as e:
        print(f"An error occurred: {e}")
```

### Asynchronous Client

An asynchronous client example using `aiohttp`.

```python
import aiohttp
import asyncio
import os

async def transcribe_async(file_path, quick=True, any_lang=True, server_url="http://localhost:8000"):
    """
    Asynchronous function to transcribe an audio file using the WhisperTurboAPI server.

    Args:
        file_path (str): Path to the audio file.
        quick (bool, optional): Whether to use quick mode. Default is True.
        any_lang (bool, optional): Whether to allow any language detection. Default is True.
        server_url (str, optional): URL of the transcription server.

    Returns:
        str: The transcribed text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    if not file_path.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
        raise ValueError("Unsupported audio format. Use WAV, MP3, M4A, or FLAC")

    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=os.path.basename(file_path))
            params = {
                'quick': str(quick).lower(),
                'any_lang': str(any_lang).lower()
            }

            async with session.post(f"{server_url}/transcribe", data=data, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['text']
                else:
                    error_detail = await response.text()
                    raise Exception(f"Error: {response.status} - {error_detail}")

# Example usage
if __name__ == "__main__":
    async def main():
        audio_file = 'path/to/audio.wav'
        try:
            transcription = await transcribe_async(audio_file, quick=False, any_lang=True)
            print("Transcription:")
            print(transcription)
        except Exception as e:
            print(f"An error occurred: {e}")

    asyncio.run(main())
```

### CURL

You can use `curl` to test the API. Here's a working example:

```bash
curl -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/audio.wav" \
  http://localhost:8000/transcribe
```

For example with a sample audio file:
```bash
curl -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_audio.wav" \
  http://localhost:8000/transcribe
```

The response will be JSON formatted:
```json
{
    "text": "Transcribed text here...",
    "elapsed_time": 1.44,
    "quick_mode": true,
    "any_lang": true
}
```

## API Reference

### POST /transcribe

Transcribe an audio file.

**Headers**:
- `Content-Type: multipart/form-data` (required)

**Parameters**:
- `file` (form data, required): Audio file (WAV, MP3, M4A, FLAC)

**Example Request**:
```bash
curl -X POST \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  http://localhost:8000/transcribe
```

**Response**:
```json
{
    "text": "The transcribed text will appear here...",
    "elapsed_time": 1.44,
    "quick_mode": true,
    "any_lang": true
}
```

**Status Codes**:
- `200 OK`: Successful transcription
- `400 Bad Request`: Invalid file format or missing file
- `500 Internal Server Error`: Server processing error

### GET /health

Check server status.

**Response**:

```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

## Demo:

For testing, example clients are provided in:

- `examples/demo.py`: Demonstrates both synchronous and asynchronous client
- `examples/simple_demo.py`: Basic synchronous client

## License

MIT License

## Acknowledgements

Based on `whisper-turbo-mlx` by JosefAlbers, which provides a fast and lightweight implementation of the Whisper model using MLX.
