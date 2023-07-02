from ast import Tuple
import os
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from chatgptHelpers.services.openaiwrapper import get_whisper_transcript

from helpers import *
from redis_wrapper import get_cached_transcript, set_cached_transcript, lock_transcript, release_transcript_lock

from video_processing import *

def create_whisper_transcript(id: str, default_to_cached=True) -> str:
    # Use the cached result if we want the cached result and one exists
    # No need to lock here because we're just pulling from Redis
    cached_result = get_cached_transcript(id)
    if default_to_cached and cached_result:
        return cached_result

    # Acquire lock, attempt to use cached result again if lock acquisiton fails
    lock = lock_transcript(id, blocking=False)
    
    try:
        # This thread is first one to acquire the lock for this ID, generate the transcript
        if lock: 
            download_video_mp3(id)
            # Creates whisper transcript from known audio location
            transcript = get_whisper_transcript(to_audio_location(id))
            set_cached_transcript(id, transcript)
            delete_video_mp3(id)
        else: 
            # Another thread is generating the transcript, wait for it to finish and then use the cached result
            lock = lock_transcript(id, blocking=True)
            transcript = get_cached_transcript(id)
    finally: 
        release_transcript_lock(lock)
    
    if not transcript:
        # TODO: Add telemetry here
        raise Exception("Failed to generate transcript for video id: {}".format(id))
    return transcript


def get_youtube_str_transcript(id: str, prefer_cached_transcript: bool = True) -> Tuple(str, bool):
    """
    Get the transcript of a video from the video ID. Uses YouTube Transcript API.
    Strips out '\n' characters.

    Returns: Transcript and a bool representing if the transcript was successfully pulled from YouTube Transcript API

    Raises: 
        Exception if YouTube Transcript API fails to find a transcript.
    """
    
    # Check if transcript is cached, use it if we prefer cached transcripts (currently cached transcripts are whisper transcripts)
    cached_transcript = get_cached_transcript(id)
    if cached_transcript and prefer_cached_transcript:
        return cached_transcript, False

    transcript = None
    try:
        transcript = YouTubeTranscriptApi.list_transcripts(
            id).find_manually_created_transcript(["en", "en-US"]).fetch()
    except Exception as e:
        print("YouTube Transcript API failed to find a transcript for video id: {}. Falling back to Whisper transcript generation".format(id))
        return None, False
    transcript_text = " ".join([item["text"] for item in transcript])
    transcript_text = transcript_text.replace("\n", " ")
    transcript_text = ''.join(
        char for char in transcript_text if char in printable)

    return transcript_text, True
