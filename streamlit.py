from main import *
from helpers import *
from video_processing import *

import json
import streamlit as st
import time 

@st.cache_data(persist=True, max_entries=20000)
def get_gpt_input_shim(prompt: str, text: str) -> str:
    """
    This shim is here to cache the GPT input so that we don't have to wait for it to generate every time.
    I wanted to avoid using streamlit outside this file.
    """
    return get_gpt_input(prompt, text)

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
            gpt_feedback = get_gpt_input_shim(summarization_prompt, transcript)
            

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
            st.sidebar.info("Answer crafted in {:.2f} seconds.".format(elapsed_time))
    return elapsed_time




def main():
    """
    stochasticity
    Badabing Streamlit Version
    
    Generates an answer to a user's query by scraping relevant web pages, generating embeddings, searching the index for relevant snippets, and piecing together an answer from the snippets.
    """
    st.title("Tubes Clues")
    # st.text("LLM Augmented Web Search")
    # Center the bing_query text input on the page
    st.markdown("""<style>.reportview-container .markdown-text { text-align: center; }</style>""", unsafe_allow_html=True)
    video_url = st.text_input("Enter video URL: ", placeholder="", key="video_url")
    # prompt_selector = st.checkbox("Use alternate prompt")
    # prompt_selector = st.select_slider(
    #     "",
    #     options=["3.5", "4"],
    #     value="3.5"
    # )
    summarization = False

    st.write("Click button for chosen flow: ")
    if st.button("General Summarization"):
        summarization = True

    # Nothing has happened yet, no error message needed (not summarization included because URL needs to be filled when button pressed)
    if (video_url == "" and not summarization):
        return

        # This part of the flow is actually general. 
        # It is under the "General Summarization" button to avoid recalculating each time focus is changed from/to the webpage.
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

    transcript = None
    start_time = time.time()
    

    # Generate search queries
    with st.spinner("Creating transcript for video..."):
        try: 
            transcript = create_whisper_transcript(video_id)
            elapsed_time = time.time() - start_time
            elapsed_time_total += elapsed_time
            st.sidebar.info("Transcript retrieved in {:.2f} seconds.".format(elapsed_time))
        except: 
            st.error("Could not create transcript for video.")
            return
    
    with st.expander("Video Transcript", expanded=False): 
        st.write(transcript)

    if summarization:
        time_for_summarization_flow = summarization_flow(transcript)
        elapsed_time_total += time_for_summarization_flow
        
    st.sidebar.info("The total flow took {:.2f} seconds.".format(elapsed_time_total))

if __name__ == '__main__':
    main()