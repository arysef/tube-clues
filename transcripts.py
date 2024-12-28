import logging
import math
import os
import time
import json
from typing import Optional, List

from redis_wrapper import value_cache as r, QUEUE_NAME

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
QUEUE_NAME = "transcript_queue"
POLL_INTERVAL = 0.5         # seconds between polls
MAX_POLL_TIME = 60.0        # max seconds to wait for the transcript
MAX_JOBS_IN_FLIGHT = 5      # max queued or in_progress jobs allowed

def get_transcript(video_id: str, task_type: str):
    """
    Steps:
      1) Always check the "audio" transcript in cache first.
      2) Then check the "youtube" transcript in cache.
      3) If neither is found, enqueue a job (if not already queued) for the requested task_type.
      4) Poll for the result until found or time-out.
    """

    # --- 1) Check for audio transcript in Redis ---
    audio_key = f"transcript:audio:{video_id}"
    audio_data = r.get(audio_key)
    if audio_data:
        logging.info(f"[User] Found existing audio transcript in cache for video ID: {video_id}.")
        return audio_data

    # --- 2) If no audio transcript, check for youtube transcript in Redis ---
    youtube_key = f"transcript:youtube:{video_id}"
    youtube_data = r.get(youtube_key)
    if youtube_data:
        logging.info(f"[User] Found existing youtube transcript in cache for video ID: {video_id}.")
        return youtube_data

    jobs_in_queue = r.llen(QUEUE_NAME)
    if jobs_in_queue >= MAX_JOBS_IN_FLIGHT:
        logging.error(f"[User] Too many jobs in the queue ({jobs_in_queue}). Rejecting new job.")
        raise RuntimeError("Transcript queue is full. Please try again later.")

    # --- 3) If no transcript, see if job is already queued or in progress for the requested task_type ---
    status_key = f"transcript_status:{task_type}:{video_id}"

    status_val = r.get(status_key)
    if not status_val:
        # Mark job as queued
        r.set(status_key, "queued", ex=60 * 60)

        job_payload = {
            "video_id": video_id,
            "task_type": task_type  # "audio" or "youtube"
        }

        r.rpush(QUEUE_NAME, json.dumps(job_payload))
        logging.info(f"[User] Enqueued job for video ID: {video_id}, task type: {task_type}.")

    # --- 4) Poll for transcript, up to MAX_POLL_TIME seconds ---
    start_time = time.time()
    while True:
        # Even while polling, re-check both audio and youtube keys, 
        # because worker might fall back automatically.
        audio_data = r.get(audio_key)
        if audio_data:
            logging.info(f"[User] Returning fallback audio transcript for video ID: {video_id}")
            return audio_data

        youtube_data = r.get(youtube_key)
        if youtube_data:
            logging.info(f"[User] Returning fallback youtube transcript for video ID: {video_id}")
            return youtube_data

        elapsed = time.time() - start_time
        if elapsed > MAX_POLL_TIME:
            logging.warning(f"[User] Timed out waiting for transcript for video ID: {video_id}")
            return None

        if (int(elapsed) % 5) == 0:
            logging.info(f"[User] Waiting for transcript... {int(elapsed)}s elapsed for video ID: {video_id}")
        time.sleep(POLL_INTERVAL)

    # If somehow we exit, we never found it
    return None
