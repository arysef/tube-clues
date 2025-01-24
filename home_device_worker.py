# home_device_worker.py

import os
import time
import json
import logging
from datetime import datetime
from string import printable
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq

from redis_wrapper import value_cache, QUEUE_NAME, WORKER_HEARTBEAT
from helpers import to_audio_location
from video_processing import download_video_mp3

logging.basicConfig(level=logging.INFO)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
assert GROQ_API_KEY is not None, "GROQ_API_KEY environment variable is not set."
groq_client = Groq(api_key=GROQ_API_KEY)

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
        transcript_text = "".join(ch for ch in transcript_text if ch in printable)
        return transcript_text
    except Exception:
        logging.warning(f"YouTube Transcript API failed for video_id: {video_id}")
        return None

def create_whisper_transcript(video_id: str, model: str = "whisper-large-v3") -> str:
    """
    Generate a transcript using Groq's Whisper v3 API.
    
    :param video_id: The video ID of the YouTube video we want to create a transcript for.
    :param model: The model to use. Default is 'whisper-large-v3'.
    :return: The transcript text generated by Whisper.
    :raises Exception: If the file isn't found or any unexpected error occurs.
    """
    download_video_mp3(video_id)
    file_path = to_audio_location(video_id)
    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB
        logging.info(f"File size for {file_path}: {file_size_mb:.2f} MB")

        with open(file_path, "rb") as audio_file:
            logging.info(f"Starting transcription for: {file_path}")
            start_time = time.time()

            # Make the API call
            transcript = groq_client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
            
            end_time = time.time()
            logging.info(f"Transcription completed in {end_time - start_time:.2f} seconds for {file_path}")

            return transcript.text

    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        raise Exception(f"File not found: {file_path}") from e

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise Exception(f"An unexpected error occurred: {str(e)}") from e
    finally:
        # Clean up the audio file
        if os.path.exists(file_path):
            os.remove(file_path)

def process_job(video_id: str, task_type: str):
    """
    Executes the correct transcription method based on task_type.
    If the first attempt fails or returns None, fallback to the other method.
    If everything fails, set transcript_status to 'failed' in Redis.
    """
    status_key = f"transcript_status:{task_type}:{video_id}"
    value_cache.set(status_key, "in_progress")

    # Determine fallback order
    if task_type == "audio":
        fallback_order = ["audio", "youtube"]
    else:
        fallback_order = ["youtube", "audio"]

    transcript = None
    final_method_used = None

    # Try each method in fallback_order until we succeed
    for method in fallback_order:
        logging.info(f"[Worker] Attempting transcription with method '{method}' for video ID: {video_id}")
        try:
            logging.info(f"[Worker] Attempting method '{method}' for video_id={video_id}")
            if method == "audio":
                transcript = create_whisper_transcript(video_id)
            else:
                transcript = get_youtube_str_transcript(video_id)

            if transcript:
                final_method_used = method
                break
            else:
                logging.warning(f"[Worker] Method '{method}' failed or returned no transcript for video_id={video_id}")

        except Exception as e:
            logging.exception(f"[Worker] Exception using method '{method}' for video={video_id}: {e}")

    if transcript and final_method_used:
        # Save the transcript
        transcript_key = f"transcript:{final_method_used}:{video_id}"
        value_cache.set(transcript_key, transcript, ex=60 * 60 * 24 * 7)  # e.g. 7 days
        logging.info(f"[Worker] Stored {final_method_used} transcript for {video_id}")

        # Remove the status key or set to something meaning "complete"
        value_cache.delete(status_key)
    else:
        # Both fallback methods failed
        logging.error(f"[Worker] Both fallback methods failed. Marking video_id={video_id} as failed.")
        value_cache.set(status_key, "failed")

def main_loop():
    logging.info("Worker started. Listening for tasks...")
    SLEEP_TIME = 5 * 60  # 5 minutes
    while True:
        # Keep heartbeat alive
        value_cache.setex(WORKER_HEARTBEAT, SLEEP_TIME, "alive")

        # BLPOP blocks until there's a job
        logging.info(f"Waiting for new jobs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result = value_cache.blpop([QUEUE_NAME], timeout=SLEEP_TIME)
        if not result:
            continue

        _, raw_data = result
        try:
            job_data = json.loads(raw_data)
            video_id = job_data["video_id"]
            task_type = job_data["task_type"]
            logging.info(f"Picked up job: {video_id}, task_type={task_type}")
            start_time = time.time()

            process_job(video_id, task_type)

            logging.info(f"Job completed in {time.time() - start_time:.2f}s for video_id={video_id}")

        except Exception as e:
            logging.exception(f"Error decoding job data or processing job: {raw_data}, {e}")

def run_worker():
    while True:
        try:
            main_loop()
        except Exception as e:
            logging.exception(f"Worker loop crashed. Restarting in 1sec... {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_worker()
