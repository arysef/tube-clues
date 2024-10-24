import logging
import math
import os
import time
from typing import Optional, List
import concurrent.futures as concurrency
import concurrent.futures as futures

from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment
import openai

from helpers import *
from redis_wrapper import cache_azure_redis
from video_processing import *

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
assert OPENAI_API_KEY is not None
openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
client = openai.OpenAI()

def get_whisper_transcript(file_path, model="whisper-1"):
    """
    Generate a transcript using OpenAI's Whisper transcript API.

    Args: 
        file_path: The file path of the mp3 being passed in.
        model: The model to use. As of this comment, only whisper-1 is available on OpenAI endpoint.

    Raises: 
        Exception if OpenAI API call fails.
    """
    try:
        with open(file_path, "rb") as audio_file:
            print("Starting transcription...")
            start_time = time.time()

            # Make the API call
            transcript = client.audio.transcriptions.create(model=model, file=audio_file)
            
            end_time = time.time()
            print(f"Transcription completed in {end_time-start_time:.2f} seconds.")
            
            return transcript.text

    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        raise Exception(f"File not found: {file_path}") from e

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise Exception(f"An unexpected error occurred: {str(e)}") from e


def split_transcript(id: str, format="mp3") -> List[str]:
    """
    Splits the transcript into 24MB chunks to allow processing by Whisper.
    """
    try: 
        audio_location = to_audio_location(id)
        audio = AudioSegment.from_mp3(audio_location)

        chunk_duration_ms = 1e6 # A little over 3 minutes
        print(chunk_duration_ms)
        num_chunks = math.ceil(len(audio) / chunk_duration_ms)
        print(num_chunks)
        chunks = []
        for i in range(num_chunks):
            start_ms = i * chunk_duration_ms
            end_ms = start_ms + chunk_duration_ms
            chunk = audio[start_ms:end_ms]
            
            # Construct the chunk filename
            base, ext = os.path.splitext(audio_location)
            chunk_filename = f"{base}_chunk{i}{ext}"
            
            # Export the chunk
            chunk.export(chunk_filename, format=format)
            chunks.append(chunk_filename)
            print(f"Exported {chunk_filename}")
    except Exception as e:
        print(e)
    return chunks
    
@cache_azure_redis
def create_whisper_transcript(id: str) -> Optional[str]:
    download_video_mp3(id)
    # Time how long split_transcript takes
    start = time.time()
    chunks = split_transcript(id)
    print(f"Splitting transcript took {time.time() - start} seconds")
    transcript = ""

    with futures.ThreadPoolExecutor() as executor:
        future_objects = [executor.submit(get_whisper_transcript, chunk) for chunk in chunks]        
        for future in future_objects:
            try:
                chunk_txt = future.result()
                transcript += chunk_txt
            except Exception as e:
                print(e)
        print("Transcript", transcript)
    for chunk in chunks:
        os.remove(chunk)

        # return None

    print("Transcript", transcript)
    return transcript


def get_youtube_str_transcript(id: str) -> Optional[str]:
    """
    Get the transcript of a video from the video ID. Uses YouTube Transcript API.
    Strips out '\n' characters.

    Returns: Transcript and a bool representing if the transcript was successfully pulled from YouTube Transcript API

    Raises: 
        Exception if YouTube Transcript API fails to find a transcript.
    """
    transcript = None
    try:
        transcript = YouTubeTranscriptApi.list_transcripts(
            id).find_manually_created_transcript(["en", "en-US"]).fetch()
    except Exception as e:
        print("YouTube Transcript API failed to find a transcript for video id: {}. Falling back to Whisper transcript generation".format(id))
        return None
    transcript_text = " ".join([item["text"] for item in transcript])
    transcript_text = transcript_text.replace("\n", " ")
    transcript_text = ''.join(
        char for char in transcript_text if char in printable)

    return transcript_text
