import json
import time
import datetime
import logging
import streamlit as st

from redis_wrapper import worker_alive
from helpers import escape_all_markdown, escape_unexpected_markdown
from prompts import get_title_question, get_custom_flow, get_fact_finding_input, get_bias_flow
from transcripts import get_transcript
from video_processing import extract_video_id, get_video_title, get_video_duration

# Configure logging for debugging or info as needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Page config and footer styling
st.set_page_config(page_title="Tube Clues", page_icon="data/magnifying-glass.png")

FOOTER_HTML = """
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
""".format("Pink Pony Club")

def parse_json_data(json_data: str):
    """
    Safely parse JSON from a string. 
    Returns: (parsed_dict, error_message) 
      - parsed_dict: The dict if parsing succeeded, else None
      - error_message: String containing error message if parsing failed, else None
    """
    cleaned_data = json_data.lstrip('\ufeff').strip()
    try:
        return json.loads(cleaned_data), None
    except json.JSONDecodeError as e:
        st.error("Could not parse results from model.")
        with st.expander("Error Details", expanded=False):
            st.write(e)
        st.write("Raw JSON From Model: ")
        st.write(cleaned_data)
        logging.error(f"JSON parsing failed: {str(e)}")
        return None, str(e)

def title_flow(transcript: str, video_id: str) -> float:
    """
    Display the video title and simulate a 'clickbait' check or discussion.
    
    Returns the elapsed time (in seconds) for this flow.
    """
    start_time = time.time()
    title = get_video_title(video_id)
    st.markdown(f"**Title:** {title}")
    question = get_title_question(title)

    with st.spinner("Processing request..."):
        st.markdown(f"**Question Asked:** {question}")
        stream_text = st.markdown("")
        for completion_text in get_custom_flow(question, transcript):
            stream_text.markdown(escape_unexpected_markdown(completion_text))
            time.sleep(0.05)

    return time.time() - start_time

def fact_finding_flow(transcript: str) -> float:
    """
    Demonstration of fact-finding flow.
    
    Returns the elapsed time (in seconds).
    """
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

def bias_flow(transcript: str) -> float:
    """
    Demonstration of bias-flow.
    
    Returns the elapsed time (in seconds).
    """
    with st.spinner("Searching video..."):
        start_time = time.time()
        raw = get_bias_flow(transcript)
        results, error = parse_json_data(raw)
        if error:
            return time.time() - start_time

        st.write("**Political Bias**")
        st.write(results["political_bias"])
        
        st.write("**Unsubstantiated Claims**")
        st.write(results["unsubstantiated_claims"])

        st.write("**Targeted Statements Against Following Groups:**")
        for bias_obj in results["targeted_statements"]:
            with st.expander(bias_obj["target"], expanded=False):
                st.write(f"Summary: {bias_obj['summary']}")
                st.write("Statements:")
                for statement in bias_obj["statements"]:
                    st.write(f"  - \"{statement}\"")

    return time.time() - start_time

def custom_flow(prompt: str, transcript: str) -> float:
    """
    Execute a custom flow based on user-provided prompt.
    
    Returns elapsed time (in seconds).
    """
    start_time = time.time()
    with st.spinner("Processing request..."):
        stream_text = st.markdown("")
        for completion_text in get_custom_flow(prompt, transcript):
            stream_text.markdown(escape_unexpected_markdown(completion_text))
            time.sleep(0.05)
    return time.time() - start_time

def transcript_creation_flow(video_id: str) -> str:
    """
    Retrieve or create a Whisper transcript for the video, showing a Streamlit spinner while in progress.
    """
    with st.spinner("Creating transcript for video..."):
        try:
            transcript = get_transcript(video_id, "audio")
            if not transcript:
                st.error("Could not create transcript for video.")
                return ""
        except Exception as e:
            st.error("Could not create transcript for video.")
            logging.error(f"Transcript creation error: {str(e)}")
            return ""
    return transcript


def init_query_params():
    """Initialize st.session_state from st.query_params."""
    q = st.query_params
    
    # Instead of storing full URL, store only the video ID in query param "vid"
    stored_video_id = q.get("vid", "")
    reconstructed_url = f"https://www.youtube.com/watch?v={stored_video_id}" if stored_video_id else ""

    # Use .setdefault() for session state
    st.session_state.setdefault("video_url", reconstructed_url)
    st.session_state.setdefault("allow_youtube_captions", q.get("captions", "true").lower() == "true")
    st.session_state.setdefault("flow_param", q.get("flow", ""))
    st.session_state.setdefault("custom_prompt", q.get("prompt", ""))
    # Keep an "old_video_url" for flow resets
    st.session_state.setdefault("old_video_url", st.session_state["video_url"])


def sync_query_params():
    """Synchronize st.session_state back to st.query_params."""
    q = st.query_params

    # Extract video ID from the current video_url and store it in "vid"
    video_url = st.session_state["video_url"].strip()
    video_id = extract_video_id(video_url)

    if video_id:
        q["vid"] = video_id
    else:
        q.pop("vid", None)

    # Keep the rest of your settings in the query params
    if st.session_state["allow_youtube_captions"]:
        q.pop("captions", None)
    else:
        q["captions"] = "false"

    flow_param = st.session_state["flow_param"].strip()
    if flow_param:
        q["flow"] = flow_param
    else:
        q.pop("flow", None)

    custom_prompt = st.session_state["custom_prompt"].strip()
    if flow_param == "custom" and custom_prompt:
        q["prompt"] = custom_prompt
    else:
        q.pop("prompt", None)


def reset_flow_if_new_url():
    """
    Callback invoked whenever the video_url text input changes.
    If the user typed a different URL than 'old_video_url',
    reset flow_param (and optionally custom_prompt).
    """
    old_url = st.session_state.get("old_video_url", "")
    new_url = st.session_state["video_url"].strip()
    if new_url != old_url:
        st.session_state["flow_param"] = ""
        st.session_state["old_video_url"] = new_url


def main():
    logging.info("Starting Tube Clues...")
    init_query_params()

    if not worker_alive():
        st.warning("Worker is out for lunch, only previously cached transcripts will work")
        _, cent_co, _ = st.columns(3)
        with cent_co:
            st.image("data/amigo.png", use_column_width=True)

    st.title("Tube Clues")
    st.markdown(
        """<style>.reportview-container .markdown-text { text-align: center; }</style>""",
        unsafe_allow_html=True
    )

    # Video URL input: attach on_change callback
    st.text_input(
        "Enter video URL: ",
        placeholder="",
        key="video_url",
        on_change=reset_flow_if_new_url
    )

    st.checkbox(
        "Prefer YouTube Caption Usage",
        help=(
            "Using existing captions from YouTube can be faster if a manually generated "
            "transcript is available and a generated one is not cached in TubeClues."
        ),
        key="allow_youtube_captions"
    )

    st.write("Click button for chosen flow: ")
    col1, col2, col3 = st.columns([1, 1, 1], gap="small")
    with col1:
        clickbait_button = st.button("Clickbait", use_container_width=True)
    with col2:
        custom_button = st.button("Custom Prompt", use_container_width=True)
    with col3:
        bias_button = st.button("Bias", use_container_width=True)

    # If a button is pressed, set the flow
    if clickbait_button:
        st.session_state["flow_param"] = "clickbait"
    elif custom_button:
        st.session_state["flow_param"] = "custom"
    elif bias_button:
        st.session_state["flow_param"] = "bias"

    st.text_input(
        "Enter custom prompt: ",
        placeholder="What's the recipe?",
        key="custom_prompt"
    )

    # If user typed a prompt, auto-switch to custom flow unless we just clicked another button
    if st.session_state["custom_prompt"].strip() and not (clickbait_button or bias_button):
        st.session_state["flow_param"] = "custom"

    # Determine which flow is active
    flow_param = st.session_state["flow_param"]
    clickbait = (flow_param == "clickbait")
    bias = (flow_param == "bias")
    custom = (flow_param == "custom")
    button_clicked = (clickbait or bias or custom)

    video_url = st.session_state["video_url"].strip()
    if not video_url and not button_clicked:
        sync_query_params()
        return

    if custom and not st.session_state["custom_prompt"].strip():
        st.error("A prompt is required for the question answering flow.")
        sync_query_params()
        return

    # Validate URL
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid video URL.")
        sync_query_params()
        return

    # Validate length
    duration = get_video_duration(video_id)
    max_duration = datetime.timedelta(minutes=60)
    if duration > max_duration:
        st.error(f"Video duration of {duration} is too long. Maximum supported duration is {max_duration}.")
        sync_query_params()
        return
    if duration > datetime.timedelta(minutes=10):
        st.warning("Video duration is over 10 minutes, processing time may be extended.")

    # Retrieve transcript
    start_time = time.time()
    transcript = None
    retrieved_transcript_from_captions = False

    if st.session_state["allow_youtube_captions"]:
        with st.spinner("Retrieving transcript for video from YouTube..."):
            transcript = get_transcript(video_id, "youtube")
            if transcript:
                retrieved_transcript_from_captions = True

    if not transcript:
        transcript = transcript_creation_flow(video_id)
    if not transcript:
        st.error("Transcript creation failed.")
        sync_query_params()
        return

    transcript_elapsed_time = time.time() - start_time
    st.sidebar.info(f"Transcript retrieved in {transcript_elapsed_time:.2f} seconds.")

    # Display transcript
    transcript_title = (
        "Video Transcript (Retrieved From YouTube)"
        if retrieved_transcript_from_captions
        else "Video Transcript (Generated from Video Audio)"
    )
    with st.expander(transcript_title, expanded=False):
        st.write(escape_all_markdown(transcript))

    # Execute the chosen flow
    flow_elapsed_time = 0.0
    if clickbait:
        flow_elapsed_time = title_flow(transcript, video_id)
    elif bias:
        flow_elapsed_time = bias_flow(transcript)
    elif custom:
        prompt_text = st.session_state["custom_prompt"].strip()
        if 1 <= len(prompt_text) <= 250:
            flow_elapsed_time = custom_flow(prompt_text, transcript)
        else:
            st.error("Custom prompt must be between 1 and 250 characters.")

    st.sidebar.info(f"Answer crafted in {flow_elapsed_time:.2f} seconds.")
    total_time = flow_elapsed_time + transcript_elapsed_time
    st.sidebar.info(f"The total flow took {total_time:.2f} seconds.")

    if not button_clicked:
        st.info("For additional processing, please select an option above.")

    # Sync final state
    sync_query_params()

if __name__ == '__main__':
    main()
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)
