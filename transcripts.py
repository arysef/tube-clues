from ast import Tuple
import os
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from chatgptHelpers.services.openaiwrapper import get_whisper_transcript

from helpers import *
from redis_wrapper import cache_azure_redis

from video_processing import *

@cache_azure_redis
def create_whisper_transcript(id: str) -> str:
    download_video_mp3(id)
    try:
        transcript = get_whisper_transcript(to_audio_location(id))
    finally:
        delete_video_mp3(id)
    
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
