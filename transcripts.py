import os
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from chatgptHelpers.services.openaiwrapper import get_chat_completion, get_whisper_transcript

from helpers import *
from video_processing import *


def get_cached_transcript(id: str) -> Optional[str]:
    """
    Get the transcript of a video from the video ID if the transcript is cached.
    """
    try:
        with open(to_transcript_location(id), "r") as f:
            print("Successfully opened cached transcript for video id: {}".format(id))
            return f.read()
    except Exception as e:
        print("Could not find cached transcript for video {}".format(to_transcript_location(id)))
        return None


def set_cached_transcript(id: str, transcript: str):
    if not os.path.exists(cached_transcripts_folder):
        os.makedirs(cached_transcripts_folder)
        print(f"Folder '{cached_transcripts_folder}' created.")

    full_file_path = to_transcript_location(id)

    with open(full_file_path, "w") as file:
        file.write(transcript)
        print("Successfully wrote transcript for video id: {}".format(id))

def create_whisper_transcript(id: str, default_to_cached=True) -> str:
    # Use the cached result if we want the cached result and one exists
    cached_result = get_cached_transcript(id)
    if default_to_cached and cached_result:
        return cached_result
        
    # Downloads video
    download_video_mp3(id)
    # Creates whisper transcript from known audio location
    transcript = get_whisper_transcript(to_audio_location(id))
    set_cached_transcript(id, transcript)
    return transcript

def get_youtube_str_transcript(id: str) -> str:
    """
    Get the transcript of a video from the video ID. Uses YouTube Transcript API.
    Strips out '\n' characters.

    Raises: 
        Exception if YouTube Transcript API fails to find a transcript.
    """
    # Check if transcript is cached
    cached_transcript = get_cached_transcript(id)
    if cached_transcript:
        return cached_transcript

    transcript = YouTubeTranscriptApi.list_transcripts(
        id).find_manually_created_transcript(["en", "en-US"]).fetch()
    transcript_text = " ".join([item["text"] for item in transcript])
    transcript_text = transcript_text.replace("\n", " ")
    transcript_text = ''.join(
        char for char in transcript_text if char in printable)

    set_cached_transcript(id, transcript_text)

    return transcript_text

