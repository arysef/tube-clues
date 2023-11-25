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
  padding: 0;
}}

#page-container {{
  display: flex;
  flex-direction: column;
  min-height: 100%;
}}

main {{
  flex: 1;
}}
footer{{
    visibility:hidden;
}}
.footer {{
  position: static;
  bottom: 0;
  left: 0;
  width: 100%;
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
""".format("Good@Bad@Us")

# Helper function to parse JSON data from model and turn it into error message if needed
def parse_json_data(json_data: str):
    try:
        return json.loads(json_data), None
    except json.JSONDecodeError as e:
        st.error(f"Could not parse results from model.")
        with st.expander("Error Details", expanded=False):
            st.write(e)
        st.write("Raw JSON From Model: ")
        st.write(json_data)
        return None, str(e)

def summarization_flow(transcript: str):
    with st.spinner("Searching video for statements..."):
        start_time = time.time()
        raw_summarization = get_summarization_input(transcript)
        gpt_feedback, error = parse_json_data(raw_summarization)
        if error:
            return time.time() - start_time

        claims = gpt_feedback['overarching_claims']
        with st.container():
            st.header("Summarization: ")
            for claim in claims:
                with st.expander(claim["claim"], expanded=False):
                    st.write("Facts Claimed in Video: ")
                    for fact in claim["supporting_facts"]:
                        st.write(f"- {fact['summary']}")
                        for source in fact["sources"]:
                            st.write(f"    - \"{source}\"")
                    st.write("Opinions Expressed in Video: ")
                    for opinion in claim["supporting_opinions"]:
                        st.write(f"- {opinion['summary']}")
                        for source in opinion["sources"]:
                            st.write(f"    - \"{source}\"")


        elapsed_time = time.time() - start_time
    return elapsed_time

def fact_finding_flow(transcript: str):
    with st.container():
        start_time = time.time()
        raw = get_fact_finding_input(transcript)
        results, error = parse_json_data(raw)
        if error: 
            return time.time() - start_time

        st.write("**Ideas and Themes**")
        st.write(results["ideas_and_themes"])
        st.write("**Facts to Check:**")
        for fact in results["facts_to_check"]:
            with st.expander(fact["fact"], expanded=False):
                st.write("Sources: ")
                for source in fact["sources"]:
                    st.write(f"  - \"{source}\"")
        
        elapsed_time = time.time() - start_time
    return elapsed_time

def opinion_count_flow(transcript: str):
    start_time = time.time()
    with st.container():
        raw = get_opinion_input(transcript)
        results, error = parse_json_data(raw)
        if error:
            return time.time() - start_time

        # Proceed if no error
        st.write("**Ideas and Themes**")
        st.write(results["ideas_and_themes"])
        st.write("**Political Biases**")
        st.write(results["political_biases"])
        st.write("**Opinions:**")

        for opinion in results["opinions"]:
            with st.expander(opinion["opinion"], expanded=False):
                st.write("Sources: ")
                for source in opinion["sources"]:
                    st.write(f"  - \"{source}\"")

    return time.time() - start_time

def bias_flow(transcript: str):
    with st.spinner("Searching video..."):
        start_time = time.time()
        raw = get_bias_flow(transcript)
        results, error = parse_json_data(raw)
        if error:
            return time.time() - start_time

        # Proceed if no error
        st.write("**Political Bias**")
        st.write(results["political_bias"])
        
        st.write("**Unsubstantiated Claims**")
        st.write(results["unsubstantiated_claims"])

        st.write("**Targeted Statements Against Following Groups:**")
        for bias in results["targeted_statements"]:
            with st.expander(bias["target"], expanded=False):
                st.write(f"Summary: {bias['summary']}")
                st.write("Statements: ")
                for statement in bias["statements"]:
                    st.write(f"  - \"{statement}\"")

        return time.time() - start_time

def custom_flow(prompt: str, transcript: str):
    start_time = time.time()
    with st.spinner("Processing request..."):
        stream_text = st.markdown("")
        for completion_text in get_custom_flow(prompt, transcript):
            stream_text.markdown(completion_text)
            time.sleep(0.05)

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
    bias = False
    button_clicked = False
    
    allow_youtube_captions = st.checkbox("Prefer YouTube Caption Usage", value=True, help="Using existing captions from YouTube can be faster if a manually generated transcript is available and a generated one is not cached in TubeClues.")

    st.write("Click button for chosen flow: ")
    col1, col2, col3  = st.columns([1, 1, 1], gap="small")
    with col1: 
        summarization = st.button("Summarization", use_container_width=True)
    
    with col2:
        custom = st.button("Custom Prompt", use_container_width=True)
    
    with col3:
        bias = st.button("Bias", use_container_width=True)

    # Add other buttons here once they're added
    
    custom_prompt = ""
    prev_qry = ""
    custom_prompt = st.text_input("Enter custom prompt: ", placeholder="What's the recipe?", key="custom_prompt")
    if custom or (prev_qry != custom_prompt):
        prev_qry = custom_prompt
        custom = True
    button_clicked = summarization | custom | bias

    # This part is required regardless of chosen flow.
    # Nothing has happened yet, no error message needed
    if (video_url == "" and not button_clicked):
        return
    
    if custom and not prev_qry:
        print("Prompt required for custom flow.")
        return
    
    # Ensure that the URL is valid and that video is short enough to process
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid video URL.")
        return
    duration = get_video_duration(video_id)

    if duration > datetime.timedelta(minutes=25): 
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
    
    if custom and not summarization and not bias:
        flow_elapsed_time = 0 # TODO: Add custom prompt flow
        if prev_qry and len(prev_qry) > 0 and len(prev_qry) < 250:
            flow_elapsed_time = custom_flow(transcript, prev_qry)
        else: 
            st.error("Custom prompt must be between 1 and 250 characters.")
        # flow_elapsed_time = opinion_count_flow(transcript)
    
    if bias: 
        flow_elapsed_time = bias_flow(transcript)
    
    st.sidebar.info("Answer crafted in {:.2f} seconds.".format(flow_elapsed_time))
    elapsed_time_total = flow_elapsed_time + transcript_elapsed_time
        
    st.sidebar.info("The total flow took {:.2f} seconds.".format(elapsed_time_total))
    if not button_clicked:
        st.info("For additional processing, please select an option above.")

if __name__ == '__main__':
    main()
    st.markdown(footer,unsafe_allow_html=True)
