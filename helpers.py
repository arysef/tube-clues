import datetime
import logging
import os
import re
import requests

import openai
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

cached_transcripts_folder = "cached_transcripts"
cached_audio_folder = "cached_audio"

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
assert YOUTUBE_API_KEY is not None

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
assert OPENAI_API_KEY is not None, "OPENAI_API_KEY environment variable is not set."
openai.api_key = OPENAI_API_KEY
openai_client = openai.OpenAI()

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
            r'(?:https?://)?'                         # Optional protocol
            r'(?:www\.|m\.)?'                         # Optional www. or m.
            r'(?:youtube\.com/(?:(?:watch.*?v=)|shorts/)|youtu\.be/)'  # watch or shorts or youtu.be
            r'([\w-]+)',                              # The capturing group for VIDEO_ID
            re.IGNORECASE
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
    
def get_video_title(video_id):
    try:      
        # Make a request to the API
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()
        
        # Log detailed issues if something goes wrong
        if 'items' not in response:
            print("Error: 'items' field is missing from the API response.")
            return None
        elif len(response['items']) == 0:
            print("Error: No video found for the provided video ID. The 'items' list is empty.")
            return None
        
        # Extract and return the video title
        video_title = response['items'][0]['snippet'].get('title')
        if video_title is None:
            print("Error: 'title' field is missing in the 'snippet' of the video data.")
            return None
        
        return video_title
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    
def convert_date(date_str):
    """
    Takes mm/dd/yyyy date string and converts it to YouTube API format
    """
    if not date_str:
        return None

    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

# This is used for transcript text, where no markdown formatting is expected
def escape_all_markdown(text: str) -> str:
    # Escape special Markdown characters
    markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '!', '|', '$']
    for char in markdown_chars:
        text = text.replace(char, '\\' + char)
    return text

# This is used for AI generated text, where sometimes things like bullet points are used but $ for italics is not
def escape_unexpected_markdown(text: str) -> str:
    # Escape special Markdown characters
    markdown_chars = ['_', '`', '[', ']', '(', ')', '+', '!', '|', '$']
    for char in markdown_chars:
        text = text.replace(char, '\\' + char)
    return text
