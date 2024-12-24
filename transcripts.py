import logging
import math
import os
import time
from typing import Optional, List
import concurrent.futures as futures

from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment
import openai

from helpers import to_audio_location
from redis_wrapper import cache_azure_redis
from video_processing import download_video_mp3

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
assert OPENAI_API_KEY is not None, "OPENAI_API_KEY environment variable is not set."
openai.api_key = OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenAI API Client (Optional usage – depends on your openai package version)
# If the official library is used in modern versions,
# you might just call openai.Audio.transcribe() and not need a separate client object.
client = openai.OpenAI()

def get_whisper_transcript(file_path: str, model: str = "whisper-1") -> str:
    """
    Generate a transcript using OpenAI's Whisper API.
    
    :param file_path: The file path of the MP3 being passed in.
    :param model: The model to use. As of now, only 'whisper-1' is available on the OpenAI endpoint.
    :return: The transcript text generated by Whisper.
    :raises Exception: If the file isn't found or any unexpected error occurs.
    """
    try:
        with open(file_path, "rb") as audio_file:
            logging.info(f"Starting transcription for: {file_path}")
            start_time = time.time()

            # Make the API call
            transcript = client.audio.transcriptions.create(model=model, file=audio_file)
            
            end_time = time.time()
            logging.info(f"Transcription completed in {end_time - start_time:.2f} seconds for {file_path}")

            return transcript.text

    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        raise Exception(f"File not found: {file_path}") from e

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise Exception(f"An unexpected error occurred: {str(e)}") from e

def split_transcript(video_id: str, file_format: str = "mp3") -> List[str]:
    """
    Splits the MP3 audio file for a given video ID into chunks, ensuring each chunk is 
    small enough for Whisper to handle properly (roughly ~16 minutes each chunk).
    
    :param video_id: The YouTube video ID for which audio has already been downloaded.
    :param file_format: File format (default is 'mp3').
    :return: A list of chunk file paths.
    """
    chunks = []
    try: 
        audio_location = to_audio_location(video_id)
        audio = AudioSegment.from_mp3(audio_location)

        # ~16 minutes in milliseconds
        chunk_duration_ms = 1_000_000  
        logging.info(f"Splitting audio into {chunk_duration_ms} ms chunks...")

        num_chunks = math.ceil(len(audio) / chunk_duration_ms)
        logging.info(f"Total chunks to generate: {num_chunks}")

        for i in range(num_chunks):
            start_ms = int(i * chunk_duration_ms)
            end_ms = int(start_ms + chunk_duration_ms)
            chunk = audio[start_ms:end_ms]
            
            base, ext = os.path.splitext(audio_location)
            chunk_filename = f"{base}_chunk{i}{ext}"
            
            chunk.export(chunk_filename, format=file_format)
            chunks.append(chunk_filename)
            logging.info(f"Exported {chunk_filename}")
    except Exception as e:
        logging.error(f"Error splitting transcript: {str(e)}")

    return chunks

@cache_azure_redis
def create_whisper_transcript(video_id: str) -> Optional[str]:
    """
    Create a transcript for a given video using OpenAI's Whisper. 
    Audio is first downloaded, split, transcribed, and concatenated.
    
    :param video_id: The YouTube video ID for which the transcript is generated.
    :return: The concatenated transcript text, or None if something went wrong.
    """
    download_video_mp3(video_id)

    start = time.time()
    chunks = split_transcript(video_id)
    logging.info(f"Splitting audio took {time.time() - start:.2f} seconds")

    transcript_parts = []
    with futures.ThreadPoolExecutor() as executor:
        future_objects = [executor.submit(get_whisper_transcript, chunk) for chunk in chunks]

        for future in future_objects:
            try:
                chunk_txt = future.result()
                transcript_parts.append(chunk_txt)
            except Exception as e:
                logging.error(f"Error transcribing chunk: {str(e)}")

    # Clean up chunk files
    for chunk in chunks:
        try:
            os.remove(chunk)
        except OSError as e:
            logging.warning(f"Could not remove chunk file {chunk}: {str(e)}")

    # Combine all chunk transcripts
    transcript = "".join(transcript_parts)
    logging.info("Transcript creation complete.")
    return transcript or None

def get_youtube_str_transcript(video_id: str) -> Optional[str]:
    """
    Get the transcript of a video from the YouTube Transcript API if manually generated English 
    subtitles exist. Strips out newline characters.
    
    :param video_id: The YouTube video ID.
    :return: The transcript string if found, otherwise None.
    """
    try:
        transcript_obj = YouTubeTranscriptApi.list_transcripts(video_id).find_manually_created_transcript(["en", "en-US"])
        transcript_list = transcript_obj.fetch()
        transcript_text = " ".join([item["text"] for item in transcript_list])
        transcript_text = transcript_text.replace("\n", " ")
        # Filter out non-printable characters
        transcript_text = "".join(char for char in transcript_text if char in printable)
        return transcript_text
    except Exception:
        logging.warning(f"YouTube Transcript API failed to find a manual transcript for video id: {video_id}.")
        return None
