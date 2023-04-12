from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import json
import requests
import os
from string import printable
from isodate import parse_duration
import datetime
from time import time
from youtube_transcript_api import YouTubeTranscriptApi
from chatgptHelpers.services.openaiwrapper import get_chat_completion, get_whisper_transcript
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
assert YOUTUBE_API_KEY is not None

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
cached_transcripts_folder = "cached_transcripts"

def get_channel_id_locally(url):
    """
    Get the channel ID from the HTML of a channel page.
    Takes URL as input.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.find("meta", itemprop="channelId")['content']


def get_video_ids(channel_id, n):
    """
    Takes Channel ID and number of videos as input.
    Outputs a list of video IDs.
    """
    # Get the uploads playlist ID for the channel
    channel_content = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    # print(channel_content)
    uploads_playlist_id = channel_content["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Fetch the most recent `n` video IDs
    videos = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=n,
    ).execute()
    # print(videos)

    video_ids = [video["snippet"]["resourceId"]["videoId"]
                 for video in videos["items"]]
    return video_ids


def convert_date(date_str):
    if not date_str:
        return None

    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")


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

def get_str_transcript(id: str) -> str:
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

    transcript = YouTubeTranscriptApi.list_transcripts(id).find_manually_created_transcript(["en", "en-US"]).fetch()
    transcript_text = " ".join([item["text"] for item in transcript])
    transcript_text = transcript_text.replace("\n", " ")
    transcript_text = ''.join(char for char in transcript_text if char in printable)
    
    set_cached_transcript(id, transcript_text)
    
    return transcript_text

class VideoInfo: 
    def __init__(self, video_id, transcript): 
        self.video_id = video_id
        self.transcript = transcript

def get_videos(channel, max_results=15, start_date=None, end_date=None, require_handmade=True):
    id = get_channel_id_from_username(
        channel) if not "youtube.com" in channel else get_channel_id_locally(channel)

    channel_videos_request = youtube.search().list(
        part="snippet",
        channelId=id,
        type="video",
        maxResults=max_results,
        order="date",
        publishedAfter=convert_date(start_date),
        publishedBefore=convert_date(end_date)
    )

    video_ids = []
    missed_videos = 0

    while channel_videos_request and len(video_ids) < max_results:
        response = channel_videos_request.execute()
        for item in response['items']:
            id = item['id']['videoId']
            try: 
                transcript_text = get_str_transcript(id)
                video_ids.append(VideoInfo(id, transcript_text))

            except Exception as e: 
                # print(e)
                print("Skipping video: {} due to no manually created transcripts", to_video_url(id))
                missed_videos += 1
                continue

            

        if 'nextPageToken' in response:
            channel_videos_request = youtube.search().list_next(
                channel_videos_request, response)
        else:
            channel_videos_request = None
    print("Skipped {} videos due to no manually created transcripts".format(missed_videos))
    return video_ids

def get_cached_transcript(id: str) -> str:
    """
    Get the transcript of a video from the video ID if the transcript is cached.
    """
    try: 
        with open("{}/{}.txt".format(cached_transcripts_folder, id), "r") as f: 
            print("Successfully opened cached transcript for video id: {}".format(id))
            return f.read()
    except Exception as e: 
        # print("Could not find cached transcript for video id: {}/{}".format(id)
        return None

def set_cached_transcript(id:str, transcript: str): 
    if not os.path.exists(cached_transcripts_folder): 
        os.makedirs(cached_transcripts_folder)
        print(f"Folder '{cached_transcripts_folder}' created.")
    
    full_file_path = os.path.join(cached_transcripts_folder, id + ".txt")
    
    with open(full_file_path, "w") as file:
        file.write(transcript)
        print("Successfully wrote transcript for video id: {}".format(id))

def get_video_duration(video_id) -> datetime.timedelta:
    """
    Get a video duration from the video ID. Uses Google API.
    """
    request = youtube.videos().list(
        part="contentDetails",
        id=video_id
    )
    response = request.execute()

    if "items" in response and response["items"]:
        duration_str = response["items"][0]["contentDetails"]["duration"]
        duration = parse_duration(duration_str)
        return duration
    else:
        raise ValueError("Invalid video ID or API key")


def to_video_url(id: str) -> str:
    return f"https://www.youtube.com/watch?v={id}"


def get_gpt_input(question: str, transcript: str) -> str:
    message = "You are a journalism analysis assistant. The incoming messages will be transcripts from videos. " + question

    messages = [
        {"role": "system", "content": message},
        {"role": "user", "content": transcript},
    ]
    return get_chat_completion(messages)


if __name__ == "__main__":
    username = "vlogbrothers"

    videos = get_videos(username, 1, end_date="4/5/2023")
    # transcript = get_str_transcript(videos[0])
    if not videos: 
        print("No videos with manually created transcripts. Exiting.")
    # system_propt = \
    # """
    # The user will send messages that contain the text to analyze. Please identify unverifiable opinions, claims, or misleading statements and return those statements. The output of this will be later used to find false statements or opinions about potentially political or societal topics that are unverifiable. Include the context around the statement necessary to understand the statement. Return the output as a JSON list of statements. 

    # Example of statements to be included:
    # 1. "The world is going to a dark place" - because it is broad and opinion-based.
    # 2. "He's such a smart guy" - because it is subjective and subject to opinion.

    # Example of statements to be excluded:
    # 1. "I loved ice cream when I was a kid" - because it is personal history and not a supporting part of the argument.

     
    # """
    system_prompt = "The user will send messages that contain the text to analyze. " \
        "Your role is to identify all potentially misleading or unverifiable claims and opinions. The claims should be " \
        "ones that are used to progress a viewpoint about society, politics, governance, philosophy, or a newsworthy event. " \
        "Please return the statements as a JSON value of statements."
    # print(videos[0].transcript)
    # print("Starting GPT")
    test_transcript = "I think that the US is really going to a dark place. " \
        "There are around 330 million people in this country. " \
        "The people in charge are really showing a disgrace. On my channel, I talk about politics, " \
        "Today we're going to be talking about the US government. " \
        "I want to start with a little story, on my tenth birthday my parents had me run a race." \
        "There were no "

    print(get_gpt_input(system_prompt, test_transcript))

    # print(get_gpt_input(system_prompt, get_str_transcript("KQh1fVpMNUM")))
    # print(get_whisper_transcript("shawnryan.mp3"))