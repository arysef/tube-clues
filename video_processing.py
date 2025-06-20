from copy import deepcopy
import feedparser
from isodate import parse_duration
import logging
import os
import requests

from yt_dlp import YoutubeDL

from helpers import *

def download_video_mp3(video_id: str):
    """
    Download a video's audio as an MP3 file and stores it in cached_audio folder,
    downsampled to 16,000Hz mono.
    """
    # Skip if already downloaded
    if os.path.exists(to_audio_location(video_id)):
        print(f"Video audio cached, no download performed for video ID: {video_id}")
        return 

    video_url = to_video_url(video_id)

    # Create the audio folder if it isn't made yet
    if not os.path.exists(cached_audio_folder):
        os.makedirs(cached_audio_folder)
        print(f"Folder '{cached_audio_folder}' created.")

    filename = os.path.join(cached_audio_folder, video_id)

    # Settings for yt-dlp (verbose to view PO token status)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }
        ],
        'postprocessor_args': [
            '-ar', '16000',  # Set audio sample rate to 16,000Hz
            '-ac', '1'       # Set audio channels to mono
        ],
        'verbose': True,  # Enable verbose logging to see PO token usage
    }

    # TODO: Likely need error handling here
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    print("Audio download complete: {}".format(to_audio_location(video_id)))

def delete_video_mp3(video_id: str):
    if not os.path.exists(to_audio_location(video_id)):
        print("Video audio already non-existent: ".format(video_id))
        return 
    os.remove(to_audio_location(video_id))

def get_most_recent_video(channel_id: str):
    feed_url = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + channel_id

    feed = feedparser.parse(feed_url)
    
    most_recent_video = feed.entries[0]
    return most_recent_video


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
    print(channel_content)
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


class VideoInfo:
    def __init__(self, video_id, transcript):
        self.video_id = video_id
        self.transcript = transcript


# TODO: Re-enable using the new worker paradigm
# def get_videos(channel, max_results=15, start_date=None, end_date=None, require_handmade=True):
#     id = get_channel_id_from_username(
#         channel) if not "youtube.com" in channel else get_channel_id_locally(channel)

#     channel_videos_request = youtube.search().list(
#         part="snippet",
#         channelId=id,
#         type="video",
#         maxResults=max_results,
#         order="date",
#         publishedAfter=convert_date(start_date),
#         publishedBefore=convert_date(end_date)
#     )

#     video_ids = []
#     missed_videos = 0

#     while channel_videos_request and len(video_ids) < max_results:
#         response = channel_videos_request.execute()
#         for item in response['items']:
#             id = item['id']['videoId']
#             try:
#                 transcript_text = get_youtube_str_transcript(id)
#                 video_ids.append(VideoInfo(id, transcript_text))

#             except Exception as e:
#                 # print(e)
#                 print(
#                     "Skipping video: {} due to no manually created transcripts", to_video_url(id))
#                 missed_videos += 1
#                 continue

#         if 'nextPageToken' in response:
#             channel_videos_request = youtube.search().list_next(
#                 channel_videos_request, response)
#         else:
#             channel_videos_request = None
#     print("Skipped {} videos due to no manually created transcripts".format(missed_videos))
#     return video_ids

def get_video_duration(video_id) -> datetime.timedelta:
    """
    Get a video duration from the video ID. Uses Google API.
    """
    local_youtube = deepcopy(youtube)
    request = local_youtube.videos().list(
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