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
            # "overarching_claims": [
            #     {
            #     "claim": "Cheap Android TV boxes may contain pre-installed malware and security risks",
            #     "supporting_facts": [
            #         {
            #         "summary": "T95 and other boxes found with pre-installed backdoors",
            #         "sources": [
            #             "Desktop Echo's discovery of a pre-installed backdoor on the T95",
            #             "the T95's backdoor is only the tip of the iceberg"
            #         ]
            #         },
            #         {
            #         "summary": "Firmware-over-the-air URL points to potentially unsafe sources",
            #         "sources": [
            #             "this isn't a problem in and of itself, but with China's looser regulations, especially with respect to foreign nationals, it means that there are no guarantees that the firmware that you download will be clean or that it will even be firmware at all"
            #         ]
            #         },
            #         {
            #         "summary": "Some Android TV boxes infected with Copycat malware",
            #         "sources": [
            #             "the original infected an estimated 14 million devices and was designed primarily to generate and steal ad revenue",
            #             "almost half of them had the same core Java folder and open preferences file"
            #         ]
            #         }
            #     ],
            #     "supporting_opinions": [
            #         {
            #         "summary": "People who help with copyright circumvention may not care about other laws",
            #         "sources": [
            #             "it's important to remember that the kinds of folks who are willing to help you circumvent copyright law tend to be the same kinds of folks who don't care about other laws either, like privacy or data collection laws"
            #         ]
            #         },
            #         {
            #         "summary": "Android TV boxes might not deliver on their advertised specifications",
            #         "sources": [
            #             "only half of that will ever be usable and the system properties seem to corroborate that",
            #             "So do they have any redeeming qualities? Are they lying about what's inside the box as well? Yeah."
            #         ]
            #         }
            #     ]
            #     },
            #     {
            #     "claim": "There are affordable, safe alternatives to potentially risky Android TV boxes",
            #     "supporting_facts": [
            #         {
            #         "summary": "Chromecast with Google TV and Nvidia Shield are safe options",
            #         "sources": [
            #             "the Nvidia Shield is definitely that, offering up 1080p to 4k upscaling, regular software updates, and the ability to act as a Plex media server",
            #             "both come free of malware"
            #         ]
            #         }
            #     ],
            #     "supporting_opinions": [
            #         {
            #         "summary": "Cheap Android TV boxes are not worth the risk compared to safer alternatives",
            #         "sources": [
            #             "so for just about anyone, it's not worth the risk, especially when these things cost about the same as a Chromecast with Google TV"
            #         ]
            #         }
            #     ]
            #     }
            # ]
            # }
            # """

            print(gpt_feedback)
            gpt_feedback = json.loads(gpt_feedback)
            claims = gpt_feedback['overarching_claims']

            # Container for the results
            with st.container():
                # Add custom CSS to the container and display the "Results" header
                st.header("Results: ")
                for claim in claims:
                    with st.expander(claim["claim"], expanded=False):
                        st.write("Facts: ")
                        facts = []
                        
                        for fact in claim["supporting_facts"]:
                            facts.append("- {}".format(fact["summary"]))
                            for source in fact["sources"]:
                                facts.append("    - \"{}\"".format(source))
                        st.write('\n'.join(facts))
                        
                        st.write("Opinions: ")
                        opinions = []

                        for opinion in claim["supporting_opinions"]:
                            opinions.append("- {}".format(opinion["summary"]))
                            for source in opinion["sources"]:
                                opinions.append("    - \"{}\"".format(source))
                        st.write('\n'.join(opinions))

                    # st.write(f"- {result}")

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