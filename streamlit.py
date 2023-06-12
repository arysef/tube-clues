from ast import Tuple
from main import *
from helpers import *
from prompts import *
from transcripts import *
from video_processing import *

import json
import streamlit as st
import time 

def summarization_flow(transcript: str):
    summarization_prompt =  """
The user will send messages that contain the text to analyze. You will return a JSON object with the findings. 
Your role is to identify any overarching or "big picture" claims that are being promoted in the text. These will be returned as a JSON value called "overarching_claims".
Each of these claims should be a JSON value as well. Each should have a field called "claim" which is a summarization of what the claim is. 
The value should also have a value called "supporting_facts" which lists all facts that are facts that can be fact-checked that are used in the video. The supporting facts field should have a "summary" field with a short summarization of the supporting fact along with a "sources" field that lists all statements from the text that make this claim. 
The value should also have a field called "supporting_opinions" which lists all opinions that are used to support the overarching claim. This can also include things that could be considered facts but that are too abstract to feasibly fact check. Similar to the supporting opinions field this should have a "summary" field and "sources" field which are a summarization of the opinion and the direct quotes from the text. 
The statements in the sources fields should be included in full.
Identify all claims that could potentially be misleading or claims and opinions that are too abstract to verify that are in some way used to support the big picture claims. They should be split into the "supporting_facts" and "supporting_opinions" sections. 
If a fact or opinion is used in more than one overarching claim, it can be included in both of the claims' JSON values. Identify all overarching claims and all of the supporting facts and opinions. 
Include all relevant overarching claims along with all facts and opinions used to support the claims. 
Please return as a JSON value of "overarching_claims". There should be no indendation for the JSON formatting. 
"""

    with st.spinner("Searching video for statements..."):
            start_time = time.time()
            gpt_feedback = get_gpt_input_cached(summarization_prompt, transcript)
            

            print(gpt_feedback)
            gpt_feedback = json.loads(gpt_feedback)
            claims = gpt_feedback['overarching_claims']

            # Container for the results
            with st.container():
                # Add custom CSS to the container and display the "Results" header
                st.header("Summarization: ")
                for claim in claims:
                    with st.expander(claim["claim"], expanded=False):
                        st.write("Facts Claimed in Video: ")
                        facts = []
                        
                        for fact in claim["supporting_facts"]:
                            facts.append("- {}".format(fact["summary"]))
                            for source in fact["sources"]:
                                facts.append("    - \"{}\"".format(source))
                        st.write('\n'.join(facts))
                        
                        st.write("Opinions Expressed in Video: ")
                        opinions = []

                        for opinion in claim["supporting_opinions"]:
                            opinions.append("- {}".format(opinion["summary"]))
                            for source in opinion["sources"]:
                                opinions.append("    - \"{}\"".format(source))
                        st.write('\n'.join(opinions))
            elapsed_time = time.time() - start_time
    return elapsed_time

def fact_finding_flow(transcript: str): 
    # fact_finding_prompt = """
    # You are an expert fact checking assistant. Your job will be to find the most valuable facts to fact check in the video. I want you to find the 5 to 10 most valuable facts to fact check. 
    # These should be facts that are important to the video and that are not too abstract to feasibly fact check. If there are 
    # """
    fact_finding_prompt = """
You are an assistant to an adversarial political fact checker. The user's messages will be transcripts from videos.
Your role is to find the most valuable facts to fact check in the given transcript. 
You should carefully analyze what facts are worth checking by weighing the importance of the fact to the video and the feasibility of fact checking the claim.
This should be done by first identifying the main claims in the video and the underlying political or ideological themes that the video is promoting and then choosing the facts that can be most feasibly checked and are most likely to undercut the the conclusions, themes, opinions, and ideologies of the video is proven incorrect. 
In weighing the priority of the fact for fact checking, you should consider a number of factors: 
    - You should consider the overall argument of the video and determine how important the fact is to the argument.
    - The political biases of the speaker of the video. For example if the speaker appears to be conservative, conservative talking points should be paid particular attention. Similarly, if the speaker appears to be liberal, liberal talking points should be paid particular attenion. 
    - You should consider how important the fact is to the video's conclusion.
    - You should consider the underlying ideas and biases that the video is promoting and determine how important the fact is to those ideas.
    - Offhand comments about topics that are not directly related to the conclusion but are relevant to the underlying tone and "slant" of the video should be considered.
    - You should consider how feasible it might be to fact check the claim using Google searches.
    - You should avoid recommending facts to check that are frivolous and not relevant to the video's point, tone, opinions, or conclusion.
    - You should recommend the facts that are most likely to cut the legs out from the video's argument and tone if they are proven false.
The result should be a JSON.
The first value in the JSON should be a "ideas_and_themes" field. This field should be a paragraph explaining the speaker's political slant, the conclusions they are promoting both directly and indirectly, and any biases which the speaker is displaying in the text.
There should also be a JSON field called "facts_to_check" that contains a list of values representing the facts that should be checked.
Each fact should have a field called "fact" which is a summarization of the fact, it should also have a field called "sources" which is a list of all statements from the text that make this claim.
The statements in the sources fields should be included in full. Any required explanation can be included in other additional fields which are not the fields mentioned above. 
All relevant facts to check (up to 10) should be included.
"""
    with st.container():
        start_time = time.time()
        results = get_gpt_input_cached(fact_finding_prompt, transcript)
        results_json = json.loads(results)
        st.write("**Ideas and Themes**")
        st.write(results_json["ideas_and_themes"])
        st.write("**Facts to Check:**")

        facts_to_check = results_json["facts_to_check"]
        for fact in facts_to_check:
            with st.expander(fact["fact"], expanded=False):
                st.write("Sources: ")
                for source in fact["sources"]:
                    st.write("  - \"{}\"".format(source))
                
        # st.write(results)
    return time.time() - start_time

def opinion_count_flow(transcript: str):
    opinion_prompt = """
   You are an expert assistant to an adversarial political analyst. The user's messages will be transcripts from videos.
Your role is to find all the unsupported opinions in the given transcript. 
You should carefully analyze what opinions are worth mentioning by weighing the importance of the opinion to the video.
This should be done by first identifying the main claims in the video and the underlying political or ideological themes that the video is promoting and then choosing the opinions that are not supported by concrete facts and are most likely to undercut the the conclusions, themes, opinions, and ideologies of the video if proven incorrect. 
In weighing the priority of the opinion, you should consider a number of factors: 
    - You should consider the overall argument of the video and determine how important the opinion is to the argument.
    - The political biases of the speaker of the video. For example if the speaker appears to be conservative, conservative talking points should be paid particular attention. Similarly, if the speaker appears to be liberal, liberal talking points should be paid particular attenion. 
    - You should consider how important the opinion is to the video's conclusion.
    - You should consider the underlying ideas and biases that the video is promoting and determine how important the opinion is to those ideas. 
    - Offhand comments about topics that are not directly related to the conclusion but are relevant to the underlying tone and "slant" of the video should be considered.
    - You should consider how feasible it might be to fact check the claim using Google searches. If it is something that could not be feasibly checked and is not logically supported by hard facts that are described in the video, it is likely worth including. 
    - You should avoid recommending opinions to check that are frivolous and not relevant to the video's point, tone, opinions, underlying political views, or conclusion.
The result should be a JSON.
The first value in the JSON should be a "ideas_and_themes" field. This field should be a paragraph explaining the speaker's political slant, the conclusions they are promoting both directly and indirectly, and any biases which the speaker is displaying in the text.
There should be a JSON field called "political_biases". This field should be a short paragraph explaining political biases and lean that the speaker is displaying in the transcript. 
There should also be a JSON field called "opinions" that contains a list of values representing the opinions that were identified.
Each opinion should have a field called "opinion" which is a summarization of the opinion, it should also have a field called "sources" which is a list of all statements from the text that make this claim.
The statements in the sources fields should be included in full. Any required explanation can be included in other additional fields which are not the fields mentioned above. 
All relevant opinions to check should be included. Do not leave out any relevant opinions.
"""
    start_time = time.time()
    with st.container():
        results = get_gpt_input_cached(opinion_prompt, transcript)
        results_json = json.loads(results)
        st.write("**Ideas and Themes**")
        st.write(results_json["ideas_and_themes"])
        st.write("**Political Biases**")
        st.write(results_json["political_biases"])
        st.write("**Opinions:**")

        facts_to_check = results_json["opinions"]
        for fact in facts_to_check:
            with st.expander(fact["opinion"], expanded=False):
                st.write("Sources: ")
                for source in fact["sources"]:
                    st.write("  - \"{}\"".format(source))
                
   
    return time.time() - start_time

def bias_flow(transcript: str):
    start_time = time.time()
    results = get_bias_flow(transcript)
    print(results)
    results_json = json.loads(results)

    st.write("**Political Bias**")
    st.write(results_json["political_bias"])
    
    st.write("**Unsubstantiated Claims**")
    st.write(results_json["unsubstantiated_claims"])

    biases = results_json["targeted_statements"]
    st.write("**Targeted Statements Against Following Groups:**")
    for bias in biases:
        with st.expander(bias["target"], expanded=False):
            st.write("Summary: {}".format(bias["summary"]))
            st.write("Statements: ")
            for statement in bias["statements"]:
                st.write("  - \"{}\"".format(statement))

    return time.time() - start_time

def transcript_creation_flow(video_id: str) -> str:
    with st.spinner("Creating transcript for video..."):
        try: 
            transcript = create_whisper_transcript(video_id)
        except: 
            st.error("Could not create transcript for video.")
            return
    return transcript



def main():

    st.title("Tubes Clues")

    st.markdown("""<style>.reportview-container .markdown-text { text-align: center; }</style>""", unsafe_allow_html=True)
    video_url = st.text_input("Enter video URL: ", placeholder="", key="video_url")

    summarization = False
    opinion_count = False
    fact_checking = False
    bias = False
    button_clicked = False
    
    allow_youtube_captions = st.checkbox("Prefer YouTube Caption Usage", value=False, help="Prefers using YouTube captions instead of generating a transcript manually. Can be faster if a manually generated transcript is available on YouTube and a generated one is not cached.")

    st.write("Click button for chosen flow: ")
    col1, col2, col3, col4  = st.columns([1, 1, 1, 1], gap="small")
    with col1: 
        summarization = st.button("Summarization", use_container_width=True)
    
    with col2:
        opinion_count = st.button("Opinion Count", use_container_width=True)
    
    with col3:
        fact_checking = st.button("Fact Finding", use_container_width=True)
    
    with col4:
        bias = st.button("Bias", use_container_width=True)

    # Add other buttons here once they're added
    button_clicked = summarization | opinion_count | fact_checking | bias

    # This part is required regardless of chosen flow.
    # Nothing has happened yet, no error message needed (not summarization included because URL needs to be filled when button pressed)
    if (video_url == "" and not button_clicked):
        return

    # Ensure that the URL is valid and that video is short enough to process
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid video URL.")
        return
    
    duration = get_video_duration(video_id)

    if duration > datetime.timedelta(minutes=15): 
        st.error("Video duration of {} is too long. Maximum video duration is currently 15 minutes.".format(duration))
        return
    
    if duration > datetime.timedelta(minutes=10):
        st.warning("Video duration is over 10 minutes, processing time may be extended.")
    
    elapsed_time_total = 0

    # Create or retrieve transcript for video
    transcript = None
    start_time = time.time()
    transcript_elapsed_time = 0
    retrieved_transcript = False
    if allow_youtube_captions:
        transcript, pulled_from_youtube = get_youtube_str_transcript(video_id)
        if transcript and pulled_from_youtube:
            retrieved_transcript = True
        elif not transcript: 
            st.info("Could not find manually created YouTube transcript. Creating transcript using Whisper.")
    
    if not transcript:
        transcript = transcript_creation_flow(video_id)
    transcript_elapsed_time = time.time() - start_time
    st.sidebar.info("Transcript retrieved in {:.2f} seconds.".format(transcript_elapsed_time))

    # Display transcript
    transcript_title = "Video Transcript (Generated from Video Audio)"
    if retrieved_transcript:
        transcript_title = "Video Transcript (Retrieved From YouTube)"

    with st.expander(transcript_title, expanded=False): 
        st.write(transcript)

    # Summarization flow
    flow_elapsed_time = 0
    if summarization:
        flow_elapsed_time = summarization_flow(transcript)
    
    if opinion_count:
        flow_elapsed_time = opinion_count_flow(transcript)
    
    if fact_checking:
        flow_elapsed_time = fact_finding_flow(transcript)
    
    if bias: 
        flow_elapsed_time = bias_flow(transcript)
    
    st.sidebar.info("Answer crafted in {:.2f} seconds.".format(transcript_elapsed_time))
    elapsed_time_total += flow_elapsed_time
        
    st.sidebar.info("The total flow took {:.2f} seconds.".format(elapsed_time_total))
    if not button_clicked:
        st.info("For additional processing, please select an option above.")

if __name__ == '__main__':
    main()