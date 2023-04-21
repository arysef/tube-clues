from chatgptHelpers.services.openaiwrapper import get_chat_completion

import helpers
from transcripts import create_whisper_transcript
from video_processing import download_video_mp3, extract_video_id, get_video_ids

# "The user will send messages that contain the text to analyze. " \
#         "Your role is to identify all potentially misleading or unverifiable claims and opinions. The claims should be " \
#         "ones that are used to progress a viewpoint about society, politics, governance, philosophy, or a newsworthy event. " \
#         "Please return the statements as a JSON value of statements."
# default_prompt = """
# The user will send messages that contain the text to analyze. You will return a JSON object with the findings. 
# First your role is to identify any overarching or "big picture" claims that are being promoted in the text. These will be returned as a JSON value called "overarching_claims".
# Your role is then to identify all potentially misleading or unverifiable claims and opinions that are in some way used to support the big picture claims. 
# The claims and opinions should be ones that are used to progress a viewpoint about society, politics, governance, philosophy, or a newsworthy event.
# Please return the statements as a JSON value of statements. If there are no such statements, an empty JSON is acceptable."
# """
# default_prompt = """
# The user will send messages that contain the text to analyze. You will return a JSON object with the findings. 
# First your role is to identify any overarching or "big picture" claims that are being promoted in the text. These will be returned as a JSON value called "overarching_claims".
# Your role is then to identify all potentially misleading claims or claims and opinions that are too abstract to verify that are in some way used to support the big picture claims. 
# Please return the statements as a JSON value of statements. If there are no such statements, an empty JSON is acceptable."
# """
# default_prompt = """
# The user will send messages that contain the text to analyze. You will return a JSON object with the findings. 
# Your role is to identify any overarching or "big picture" claims that are being promoted in the text. These will be returned as a JSON value called "overarching_claims".
# Each of these claims should be a JSON value as well. Each should have a field called "claim" which is a summarization of what the claim is. 
# The value should also have a value called "supporting_facts" which lists all facts that are facts that can be fact-checked that are used in the video. The supporting facts field should have a "summary" field with a short summarization of the supporting fact along with a "sources" field that lists all statements from the text that make this claim. 
# The value should also have a field called "supporting_opinions" which lists all opinions that are used to support the overarching claim. This can also include things that could be considered facts but that are too abstract to feasibly fact check. Similar to the supporting opinions field this should have a "summary" field and "sources" field which are a summarization of the opinion and the direct quotes from the text. 
# The statements in the sources fields should be included in full.
# Identify all claims that could potentially be misleading or claims and opinions that are too abstract to verify that are in some way used to support the big picture claims. They should be split into the "supporting_facts" and "supporting_opinions" sections. 
# If a fact or opinion is used in more than one overarching claim, it can be included in both of the claims' JSON values. Identify all overarching claims and all of the supporting facts and opinions. 
# Include all relevant overarching claims along with all facts and opinions used to support the claims. 
# Please return as a JSON value of "overarching_claims". There should be no indendation for the JSON formatting. 
# """


# The claims and opinions should be ones that are used to progress a viewpoint about society, politics, governance, philosophy, or a newsworthy event.


def get_gpt_input(question: str, transcript: str) -> str:
    message = "You are a journalism analysis assistant. The incoming messages will be transcripts from videos. " + question

    messages = [
        {"role": "system", "content": message},
        {"role": "user", "content": transcript},
    ]
    return get_chat_completion(messages)


def process_video(url: str, default_to_cached_transcript=True) -> str:
    id = extract_video_id(url)
    transcript = create_whisper_transcript(id, default_to_cached_transcript)
    print(transcript)

    return get_gpt_input(default_prompt, transcript)


if __name__ == "__main__":
    username = "vlogbrothers"

    # videos = get_videos(username, 1, end_date="4/5/2023")
    # # transcript = get_str_transcript(videos[0])
    # if not videos:
    #     print("No videos with manually created transcripts. Exiting.")
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

    # print(get_gpt_input(system_prompt, test_transcript))

    # print(get_gpt_input(system_prompt, get_str_transcript("KQh1fVpMNUM")))
    # print(get_whisper_transcript("shawnryan.mp3"))

    # download_video_mp3('o4vLoZphZGs')
    # print(process_video("https://www.youtube.com/watch?v=o4vLoZphZGs", default_to_cached_transcript=False))
    # print(get_video_ids(helpers.get_channel_id_from_username("vlogbrothers"), 4))
