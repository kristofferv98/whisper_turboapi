# demo.py

import requests
import os
import logging
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def transcribe_async(audio_file_path, quick=True, any_lang=True, server_url="http://localhost:8000"):
    """
    Asynchronous transcription example using aiohttp.

    Args:
        audio_file_path (str): Path to the audio file.
        quick (bool): Quick mode (default is True).
        any_lang (bool): Allow any language detection (default is True).
        server_url (str): Server URL (default is http://localhost:8000).

    Returns:
        tuple: Transcribed text and elapsed time, or error message and None.
    """
    async with aiohttp.ClientSession() as session:
        with open(audio_file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=os.path.basename(audio_file_path))

            params = {
                'quick': str(quick).lower(),
                'any_lang': str(any_lang).lower()
            }

            async with session.post(f"{server_url}/transcribe", data=data, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['text'], result['elapsed_time']
                else:
                    error_detail = await response.text()
                    return f"Error: {response.status} - {error_detail}", None

def transcribe_sync(audio_file_path, quick=True, any_lang=True, server_url="http://localhost:8000"):
    """
    Synchronous transcription example using requests.

    Args:
        audio_file_path (str): Path to the audio file.
        quick (bool): Quick mode (default is True).
        any_lang (bool): Allow any language detection (default is True).
        server_url (str): Server URL (default is http://localhost:8000).

    Returns:
        tuple: Transcribed text and elapsed time, or error message and None.
    """
    with open(audio_file_path, 'rb') as f:
        files = {'file': (os.path.basename(audio_file_path), f, 'audio/wav')}
        params = {
            'quick': str(quick).lower(),
            'any_lang': str(any_lang).lower()
        }
        response = requests.post(f"{server_url}/transcribe", files=files, params=params)

    if response.status_code == 200:
        result = response.json()
        return result['text'], result['elapsed_time']
    else:
        error_detail = response.text
        return f"Error: {response.status_code} - {error_detail}", None

async def main():
    """
    Main function to demonstrate both synchronous and asynchronous transcription.
    """
    test_audio = "path/to/audio.wav"

    print("Transcription Examples")
    print("=====================\n")

    # Quick mode, English only (synchronous)
    print("Quick Mode, English-only Transcription:")
    text, duration = transcribe_sync(test_audio, quick=True, any_lang=False)
    if duration:
        print(f"Text: {text}")
        print(f"Duration: {duration:.2f} seconds\n")
    else:
        print(text)

    # Standard mode, any language (asynchronous)
    print("Standard Mode, Multi-language Transcription:")
    text, duration = await transcribe_async(test_audio, quick=False, any_lang=True)
    if duration:
        print(f"Text: {text}")
        print(f"Duration: {duration:.2f} seconds\n")
    else:
        print(text)

if __name__ == "__main__":
    asyncio.run(main())
