from ast import Tuple
from helpers import *
from prompts import *
from transcripts import *
from video_processing import *

import json
import streamlit as st
import time 

# Set page configuration and footer
st.set_page_config(page_title="Tube Clues", page_icon="data/magnifying-glass.png")
footer = """
<style>
html, body {{
  height: 100%;
  margin: 0;
}}

#page-container {{
  display: flex;
  flex-direction: column;
  min-height: 100%;
}}

main {{
  flex: 1;
  padding-bottom: 50px; /* adjust this value to match the height of your footer */
}}
footer{{
    visibility:hidden;
}}
.footer {{
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 50px; /* adjust this value to match the height of your footer */
  background-color: transparent;
  color: #808080;
  text-align: center;
  font-size: 0.875em;
}}

a {{
  color: #BFBFBF;
  background-color: transparent;
  text-decoration: none;
}}

a:hover, a:active {{
  color: #0283C3;
  background-color: transparent;
  text-decoration: underline;
}}
</style>

<div id="page-container">
    <div class="footer">
        <p style='font-size: 0.875em;'>{}<br 'style= top:0px;'></p>
    </div>
</div>
""".format("Carmen")
st.markdown(footer,unsafe_allow_html=True)

def summarization_flow(transcript: str):
    with st.spinner("Searching video for statements..."):
        start_time = time.time()
        gpt_feedback = get_summarization_input(transcript)        

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
    with st.container():
        start_time = time.time()
        results = get_fact_finding_input(transcript)
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
    start_time = time.time()
    with st.container():
        results = get_opinion_input(transcript)
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
    with st.spinner("Searching video..."):
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
    

def custom_flow(prompt: str, transcript: str):
    start_time = time.time()
    with st.spinner("Processing request..."):
        results = get_custom_flow(prompt, transcript)
        print(results)

        st.write(results)

    return time.time() - start_time

# Wrapper for create_whisper_transcript that shows text and spinner
def transcript_creation_flow(video_id: str) -> str:
    with st.spinner("Creating transcript for video..."):
        try: 
            transcript = create_whisper_transcript(video_id)
        except: 
            st.error("Could not create transcript for video.")
            return
    return transcript



def main():
    st.title("Tube Clues")
    st.markdown("""<style>.reportview-container .markdown-text { text-align: center; }</style>""", unsafe_allow_html=True)
    video_url = st.text_input("Enter video URL: ", placeholder="", key="video_url")

    summarization = False
    custom = False
    fact_checking = False
    bias = False
    button_clicked = False
    
    allow_youtube_captions = st.checkbox("Prefer YouTube Caption Usage", value=True, help="Using existing captions from YouTube can be faster if a manually generated transcript is available and a generated one is not cached in TubeClues.")

    st.write("Click button for chosen flow: ")
    col1, col2, col3, col4  = st.columns([1, 1, 1, 1], gap="small")
    with col1: 
        summarization = st.button("Summarization", use_container_width=True)
    
    with col2:
        custom = st.button("Custom Prompt", use_container_width=True)
    
    with col3:
        fact_checking = st.button("Fact Finding", use_container_width=True)
    
    with col4:
        bias = st.button("Bias", use_container_width=True)

    # Add other buttons here once they're added
    
    custom_prompt = None
    # custom_run = False
    # if custom or custom_run: 
    custom_prompt = st.text_input("Enter custom prompt: ", placeholder="What's the recipe?", key="custom_prompt")
        # custom_run = st.button("Run", use_container_width=True)
        # custom = custom_run

    button_clicked = summarization | custom | fact_checking | bias

    # This part is required regardless of chosen flow.
    # Nothing has happened yet, no error message needed
    if (video_url == "" and not button_clicked):
        return
    
    if custom and not custom_prompt:
        print("Prompt required for custom flow.")
        return
    
    # Ensure that the URL is valid and that video is short enough to process
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid video URL.")
        return
    duration = get_video_duration(video_id)

    if duration > datetime.timedelta(minutes=30): 
        st.error("Video duration of {} is too long. Maximum video duration is currently 15 minutes.".format(duration))
        return
    
    if duration > datetime.timedelta(minutes=10):
        st.warning("Video duration is over 10 minutes, processing time may be extended.")
    
    elapsed_time_total = 0

    # Create or retrieve transcript for video
    transcript = None
    start_time = time.time()
    transcript_elapsed_time = 0
    retrieved_transcript_from_captions = False
    if allow_youtube_captions:
        with st.spinner("Retrieving transcript for video from YouTube..."):
            transcript = get_youtube_str_transcript(video_id)
            if transcript:
                retrieved_transcript_from_captions = True
            else: 
                st.info("Could not find manually created YouTube transcript. Creating transcript using Whisper.")
    
    if not transcript:
        transcript = transcript_creation_flow(video_id)
    transcript_elapsed_time = time.time() - start_time
    st.sidebar.info("Transcript retrieved in {:.2f} seconds.".format(transcript_elapsed_time))

    # Display transcript
    transcript_title = "Video Transcript (Generated from Video Audio)"
    if retrieved_transcript_from_captions:
        transcript_title = "Video Transcript (Retrieved From YouTube)"

    with st.expander(transcript_title, expanded=False): 
        print(transcript)
        st.write(escape_markdown(transcript))

    # Summarization flow
    flow_elapsed_time = 0
    if summarization:
        flow_elapsed_time = summarization_flow(transcript)
    
    if custom:
        flow_elapsed_time = 0 # TODO: Add custom prompt flow
        if custom_prompt and len(custom_prompt) > 0 and len(custom_prompt) < 250:
            flow_elapsed_time = custom_flow(transcript, custom_prompt)
        else: 
            st.error("Custom prompt must be between 1 and 250 characters.")
        # flow_elapsed_time = opinion_count_flow(transcript)
    
    if fact_checking:
        flow_elapsed_time = fact_finding_flow(transcript)
    
    if bias: 
        flow_elapsed_time = bias_flow(transcript)
    
    st.sidebar.info("Answer crafted in {:.2f} seconds.".format(flow_elapsed_time))
    elapsed_time_total = flow_elapsed_time + transcript_elapsed_time
        
    st.sidebar.info("The total flow took {:.2f} seconds.".format(elapsed_time_total))
    if not button_clicked:
        st.info("For additional processing, please select an option above.")

if __name__ == '__main__':
    main()