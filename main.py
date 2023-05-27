from chatgptHelpers.services.openaiwrapper import get_chat_completion

import helpers
from transcripts import create_whisper_transcript
from video_processing import download_video_mp3, extract_video_id, get_video_ids


if __name__ == "__main__":
    username = "vlogbrothers"

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

