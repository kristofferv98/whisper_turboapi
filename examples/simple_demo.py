# simple_client.py

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
    # Add file existence check
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
        
    # Add file type validation
    if not file_path.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
        raise ValueError("Unsupported audio format. Use WAV, MP3, M4A, or FLAC")
        
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'audio/wav')}
        params = {
            'quick': str(quick).lower(),
            'any_lang': str(any_lang).lower()
        }
        response = requests.post(f"{server_url}/transcribe", files=files, params=params)
    if response.status_code == 200:
        return response.json()['text']
    else:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

if __name__ == "__main__":
    # Replace 'path/to/audio.wav' with the path to your audio file
    audio_file = 'path/to/audio.wav'

    # Start the transcription
    try:
        transcription = transcribe_audio(audio_file, quick=True, any_lang=False)
        print("Transcription:")
        print(transcription)
    except Exception as e:
        print(f"An error occurred: {e}")
