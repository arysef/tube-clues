# transcripts.py

import logging
import time
import json
from typing import Optional

from redis_wrapper import value_cache as r, QUEUE_NAME

# Adjust these as desired
POLL_INTERVAL = 0.5      # seconds between polls
MAX_POLL_TIME = 60.0     # max seconds to wait for the transcript
MAX_JOBS_IN_FLIGHT = 5   # max queued or in_progress jobs allowed

def get_transcript(video_id: str, task_type: str):
    """
    Steps:
      1) Check if we have an audio transcript in Redis. Return it if found.
      2) If none, check if we have a youtube transcript in Redis. Return it if found.
      3) Otherwise, we look at transcript_status:{task_type}:{video_id}.
         - If status is 'failed', let's re-queue since user is making a fresh request.
         - If no status or status in ('failed', 'queued', 'in_progress'), we queue a job or confirm it's queued.
      4) Poll for result, or see if it fails quickly.
    """

    # 1) Check for existing audio transcript
    audio_key = f"transcript:audio:{video_id}"
    audio_data = r.get(audio_key)
    if audio_data:
        logging.info(f"[User] Found existing audio transcript in cache for video ID: {video_id}.")
        return audio_data

    # 2) Check for existing youtube transcript
    youtube_key = f"transcript:youtube:{video_id}"
    youtube_data = r.get(youtube_key)
    if youtube_data:
        logging.info(f"[User] Found existing youtube transcript in cache for video ID: {video_id}.")
        return youtube_data

    # 3) If we still have no transcript, check the job status
    status_key = f"transcript_status:{task_type}:{video_id}"
    status_val = r.get(status_key)

    # If the user wants to request again, but the status is 'failed', let's re-queue
    if status_val == "failed":
        logging.warning(f"[User] Found previous 'failed' status. Attempting a fresh queue for video: {video_id}")
        status_val = None  # treat it like it’s never been queued
        # We intentionally do NOT delete the status key here, but will overwrite below

    if not status_val or status_val in ("failed", "queued", "in_progress"):
        # If we haven't queued or are forced to re-queue from previous 'failed'
        # limit queue length so we don’t blow up
        jobs_in_queue = r.llen(QUEUE_NAME)
        if jobs_in_queue >= MAX_JOBS_IN_FLIGHT:
            logging.error(f"[User] Too many jobs in the queue ({jobs_in_queue}). Rejecting new job.")
            raise RuntimeError("Transcript queue is full. Please try again later.")

        if not status_val or status_val == "failed":
            # Mark job as queued
            r.set(status_key, "queued", ex=60 * 60)

            job_payload = {
                "video_id": video_id,
                "task_type": task_type
            }
            r.rpush(QUEUE_NAME, json.dumps(job_payload))
            logging.info(f"[User] Enqueued job for video ID: {video_id}, task type: {task_type}.")

    # 4) Poll for transcript or 'failed'
    start_time = time.time()
    while True:
        # Re-check both possible transcripts
        audio_data = r.get(audio_key)
        if audio_data:
            logging.info(f"[User] Returning fallback audio transcript for video ID: {video_id}")
            return audio_data

        youtube_data = r.get(youtube_key)
        if youtube_data:
            logging.info(f"[User] Returning fallback youtube transcript for video ID: {video_id}")
            return youtube_data

        # Also check if the worker signaled 'failed'
        current_status = r.get(status_key)
        if current_status == "failed":
            logging.warning(f"[User] Worker indicated transcript generation FAILED for video: {video_id}")
            # Return None so that the caller can display a quick error
            return None

        elapsed = time.time() - start_time
        if elapsed > MAX_POLL_TIME:
            logging.warning(f"[User] Timed out waiting for transcript for video ID: {video_id}")
            return None

        time.sleep(POLL_INTERVAL)
