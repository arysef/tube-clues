from bs4 import BeautifulSoup
import datetime
from googleapiclient.discovery import build
import os
import re
import requests

cached_transcripts_folder = "cached_transcripts"
cached_audio_folder = "cached_audio"

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
assert YOUTUBE_API_KEY is not None

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_channel_id_locally(url):
    """
    Get the channel ID from the HTML of a channel page.
    Takes URL as input.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.find("meta", itemprop="channelId")['content']

def get_channel_id_from_username(username):
    """
    Get the channel ID from a channel username. Uses Google API. 
    """
    channels_response = youtube.channels().list(
        part="id",
        forUsername=username,
        maxResults=1
    ).execute()

    if channels_response["items"]:
        return channels_response["items"][0]["id"]
    else:
        print("Channel not found")
        return None

def to_video_url(id: str) -> str:
    return f"https://www.youtube.com/watch?v={id}"

def to_audio_location(id: str) -> str: 
    return os.path.join(cached_audio_folder, id + ".mp3")

def to_transcript_location(id: str) -> str:
    return os.path.join(cached_transcripts_folder, id + ".txt")

def extract_video_id(youtube_link):
    try:
        # Regular expression to match YouTube URL and extract the video ID
        pattern = re.compile(
            r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)'
        )
        match = pattern.search(youtube_link)
        
        if not match:
            raise ValueError("Invalid YouTube link")

        video_id = match.group(1)
        return video_id
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def convert_date(date_str):
    """
    Takes mm/dd/yyyy date string and converts it to YouTube API format
    """
    if not date_str:
        return None

    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

