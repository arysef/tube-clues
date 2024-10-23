# Mostly just for trying out things and impromptu testing. Real main is in streamlit.py
import helpers
import json
import redis_wrapper
from transcripts import create_whisper_transcript
import video_processing

def create_bias_comment(video_id:str) -> str: 
    transcript = create_whisper_transcript(video_id)

    statements = "*Bias Detection Bot Result:* "
    count = 0 
    results = prompts.get_bias_flow(transcript)
    print(results)
    results_json = json.loads(results)

    for target in results_json["targeted_statements"]:
        count += len(target["statements"])
    

    statements += "This video contains *" + str(count) + "* statements that may be unnecessarily biased or derogatory." + "\n"

    for target in results_json["targeted_statements"]:
        statements += "*Target:* " + target["target"] + "\n"


        for statement in target["statements"]: 
            statements += " - " + statement + "\n"
    statements += "*Summary:* " + target["summary"] + "\n"

    statements += "\n\n"
    statements += "*Overall Bias:* " + results_json["political_bias"] + "\n"

    return statements


if __name__ == "__main__":
    username = "vlogbrothers"
    # print(videos[0].transcript)
    # print("Starting GPT")
    
    fox_channel_id = "UCXIJgqnII2ZOINSWNOGFThA"
    print(fox_channel_id)

    # print(id)
    # video = video_processing.get_most_recent_video(fox_channel_id)
    # print(video.title)
    # video_id = helpers.extract_video_id("https://www.youtube.com/watch?v=GNRoXCqp6hw&t=152s")
    # results = create_bias_comment(video_id)
    # print(results)
    # redis_wrapper.test()

    # print("Transcript locked: " + str(redis_wrapper.transcript_locked(lock_name)))
    # print("Transcript locked: " + str(redis_wrapper.transcript_locked(lock_name)))
    # print("Released lock")

