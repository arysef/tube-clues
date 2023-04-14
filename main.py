from chatgptHelpers.services.openaiwrapper import get_chat_completion
from video_processing import download_video_mp3, extract_video_id
from transcripts import create_whisper_transcript

def get_gpt_input(question: str, transcript: str) -> str:
    message = "You are a journalism analysis assistant. The incoming messages will be transcripts from videos. " + question

    messages = [
        {"role": "system", "content": message},
        {"role": "user", "content": transcript},
    ]
    return get_chat_completion(messages)


def process_video(url: str) -> str:
    id = extract_video_id(url)
    download_video_mp3(id)
    transcript = create_whisper_transcript(id)
    print(transcript)

    default_prompt = "The user will send messages that contain the text to analyze. " \
        "Your role is to identify all potentially misleading or unverifiable claims and opinions. The claims should be " \
        "ones that are used to progress a viewpoint about society, politics, governance, philosophy, or a newsworthy event. " \
        "Please return the statements as a JSON value of statements."
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
    print(process_video("https://www.youtube.com/watch?v=o4vLoZphZGs"))
