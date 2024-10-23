import logging
import os
import re
import requests

from bs4 import BeautifulSoup
import datetime
from googleapiclient.discovery import build
from pytube import YouTube

cached_transcripts_folder = "cached_transcripts"
cached_audio_folder = "cached_audio"

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
assert YOUTUBE_API_KEY is not None

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)

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
        maxResults=5
    ).execute()
    for channel in channels_response["items"]:
        print(channel["id"])

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
        # Enhanced regular expression to match various YouTube URL formats including URLs with additional query parameters
        pattern = re.compile(
            r'(?:https?://)?(?:www\.|m\.)?youtube\.com/watch.*?v=([\w-]+)|youtu\.be/([\w-]+)'
        )
        match = pattern.search(youtube_link)
        
        if not match:
            raise ValueError("Invalid YouTube link")

        # Using a loop to find the first non-None group (either from the main URL or the shortened youtu.be format)
        video_id = next((group for group in match.groups() if group is not None), None)
        
        if not video_id:
            raise ValueError("No video ID found in the link")

        return video_id
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_video_title(url: str) -> str:
    try:
        yt = YouTube(url)
        return yt.title
    except Exception as e:
        logging.error(f"Failed to get video title for URL: {url} - Error: {str(e)}")
        raise Exception(f"Error retrieving video title: {str(e)}") from e

    
def convert_date(date_str):
    """
    Takes mm/dd/yyyy date string and converts it to YouTube API format
    """
    if not date_str:
        return None

    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

def escape_markdown(text: str) -> str:
    # Escape special Markdown characters
    markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '!', '|', '$']
    for char in markdown_chars:
        text = text.replace(char, '\\' + char)
    return text
