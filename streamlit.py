from main import *
from helpers import *
from video_processing import *

import json
import streamlit as st
import time 

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
    video_url = st.text_input("", placeholder="", key="video_url")
    # prompt_selector = st.checkbox("Use alternate prompt")
    # prompt_selector = st.select_slider(
    #     "",
    #     options=["3.5", "4"],
    #     value="3.5"
    # )
    
    if video_url:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("Invalid video URL.")
            return
        elapsed_time_total = 0
        # corpus_df = None
        # answer = None
        # results = None
        # results_text = None
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
        

        # Generate answer
        with st.spinner("Searching video for statements..."):
            start_time = time.time()
            gpt_feedback = get_gpt_input(default_prompt, transcript)
            # gpt_feedback = """
            # {
            # "statements": [
            #     "I know that sports are not very important.",
            #     "It is not critical to the future of humanity whether a ball goes over a line or into a cup or through a net.",
            #     "I am sympathetic to people who feel like maybe we shouldn't devote hundreds of billions of dollars and gobs of human attention to the exploits of these balls and the people who are paid to manipulate them."
            # ]
            # }
            # """

            print(gpt_feedback)
            gpt_feedback = json.loads(gpt_feedback)
            results = gpt_feedback['statements']

            # Container for the results
            with st.container():
                # Add custom CSS to the container and display the "Results" header
                st.header("Results: ")
                for result in results:
                    st.write(f"- {result}")

            elapsed_time = time.time() - start_time
            elapsed_time_total += elapsed_time
            st.sidebar.info("Answer crafted in {:.2f} seconds.".format(elapsed_time))

        # # Sort the results list by ID
        # sorted_results = sorted(results, key=lambda x: int(x.__dict__['_data_store']['id']))
        # with st.expander("Relevant sources", expanded=False):
        #     # Iterate over the sorted list
        #     for item in sorted_results:
        #         # Parse the string into a dictionary using the json module
        #         data = item.__dict__
        #         # Access the relevant fields using dictionary notation
        #         id = data.get('_data_store').get('id')
        #         source = data.get('_data_store').get('metadata').get('source')
        #         text = data.get('_data_store').get('metadata').get('text')
        #         text = re.sub(r'\[.*?\]', '', text)
        #         text = text.replace("$", "\\$")
        #         if source == 'known_entity':
        #             source = 'https://www.wikipedia.org'
        #         # Use string formatting to print the fields in a cleanly formatted way
        #         st.markdown(":red[[{}]] _<{}>_ ...{}...\n".format(id, source, str.lower(text)))
        st.sidebar.info("The total flow took {:.2f} seconds.".format(elapsed_time_total))

if __name__ == '__main__':
    main()