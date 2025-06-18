"""
Tube Clues - Streamlit Web Interface

This module implements the Streamlit web interface for the Tube Clues application,
which provides analysis of YouTube video content without requiring users to watch
the videos. It handles user input, video processing, and result display.

Features include:
- Clickbait title analysis
- Bias detection
- Custom prompt analysis
- YouTube transcript processing
- Query parameter support for sharing links
"""

import json
import time
import datetime
import logging
from typing import Dict, List, Tuple, Optional, Union, Any

import streamlit as st

from redis_wrapper import worker_alive
from helpers import escape_all_markdown, escape_unexpected_markdown
from prompts import (
    get_title_question,
    get_custom_flow,
    get_bias_flow,
    get_context_flow,
    get_sift_report
)
from transcripts import get_transcript
from video_processing import extract_video_id, get_video_title, get_video_duration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
""".format("unholy")

def parse_json_data(json_data: str) -> tuple[dict | None, str | None]:
    """
    Safely parse JSON from a string.
    
    Args:
        json_data: The JSON string to parse
        
    Returns:
        tuple: (parsed_dict, error_message)
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
    
    Args:
        transcript: The video transcript text
        video_id: The YouTube video ID
        
    Returns:
        float: Elapsed time (in seconds) for this flow
    """
    start_time = time.time()
    
    # Get video title and generate question
    title = get_video_title(video_id)
    st.markdown(f"**Title:** {title}")
    question = get_title_question(title)

    # Process and stream response
    with st.spinner("Processing request..."):
        st.markdown(f"**Question Asked:** {question}")
        stream_text = st.markdown("")
        for completion_text in get_custom_flow(question, transcript):
            stream_text.markdown(escape_unexpected_markdown(completion_text))
            time.sleep(0.05)

    return time.time() - start_time

def bias_flow(transcript: str) -> float:
    """
    Analyze and display bias information from video transcript.
    
    Args:
        transcript: The video transcript text
        
    Returns:
        float: Elapsed time (in seconds) for this flow
    """
    with st.spinner("Searching video for bias..."):
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
    
    Args:
        prompt: The custom user prompt
        transcript: The video transcript text
        
    Returns:
        float: Elapsed time (in seconds) for this flow
    """
    start_time = time.time()
    
    with st.spinner("Processing custom prompt..."):
        stream_text = st.markdown("")
        for completion_text in get_custom_flow(prompt, transcript):
            stream_text.markdown(escape_unexpected_markdown(completion_text))
            time.sleep(0.05)
            
    return time.time() - start_time

def context_flow(transcript: str) -> float:
    """
    Extract 3 claims from transcript and display as interactive buttons.
    
    Args:
        transcript: The video transcript text
        
    Returns:
        float: Elapsed time (in seconds) for this flow
    """
    start_time = time.time()
    
    # Check if claims are already cached in session state
    if 'context_claims' not in st.session_state:
        with st.spinner("Extracting key claims from video..."):
            raw = get_context_flow(transcript)
            results, error = parse_json_data(raw)
            if error:
                return time.time() - start_time
            
            # Store claims in session state for button handling
            st.session_state['context_claims'] = results['claims']
    
    # Check if a claim has been selected
    selected_claim_index = st.session_state.get('selected_claim_index', None)
    
    if selected_claim_index is not None:
        # Show the selected claim and generate report
        claim_data = st.session_state['context_claims'][selected_claim_index]
        claim = claim_data['claim']
        quotes = claim_data['quotes']
        
        st.write(f"**Providing Context for Claim:** {claim}")
        
        # Show quotes in a collapsed expander
        with st.expander("Quotes from transcript:", expanded=False):
            for quote in quotes:
                st.write(f"• \"{quote}\"")
        
        # Generate and stream the sift report
        with st.spinner("Generating fact-checking report..."):
            stream_text = st.markdown("")
            for completion_text in get_sift_report(claim, quotes, transcript):
                stream_text.markdown(escape_unexpected_markdown(completion_text))
                time.sleep(0.05)
    else:
        # Show claim selection interface
        st.write("**Key Claims from Video:**")
        
        # Check if any claims were found
        if not st.session_state['context_claims']:
            st.write("No claims were found for analyzing.")
        else:
            st.write("Click on a claim to generate a detailed fact-checking report.")
            
            # Create buttons for each claim and handle clicks
            for i, claim_data in enumerate(st.session_state['context_claims']):
                claim = claim_data['claim']
                
                # Create button for each claim
                if st.button(claim, key=f"claim_button_{i}"):
                    st.session_state['selected_claim_index'] = i
                    st.rerun()

    return time.time() - start_time

def transcript_creation_flow(video_id: str) -> str:
    """
    Retrieve or create a Whisper transcript for the video.
    
    Args:
        video_id: The YouTube video ID
        
    Returns:
        str: The video transcript text or empty string if creation failed
    """
    with st.spinner("Creating transcript for video..."):
        try:
            transcript = get_transcript(video_id, "audio")
            if not transcript:
                st.error("Transcript creation failed or worker indicated a problem.")
                
                # Provide a retry option
                if st.button("Try Again", key=f"retry_{video_id}"):
                    st.info("Re-trying transcript creation...")
                    transcript = get_transcript(video_id, "audio")
                    if not transcript:
                        st.error("Still failed. Please contact creator or try later.")
                return ""  # Return empty transcript
                
        except Exception as e:
            st.error("Could not create transcript for video (exception).")
            logging.error(f"Transcript creation error: {str(e)}")
            return ""
            
    return transcript


def init_query_params() -> None:
    """
    Initialize session state from query parameters.
    
    This function sets up the initial state of the application based on
    URL query parameters, enabling sharing and bookmarking of specific views.
    """
    q = st.query_params
    
    # Extract video ID from the URL query parameter
    stored_video_id = q.get("vid", "")
    reconstructed_url = f"https://www.youtube.com/watch?v={stored_video_id}" if stored_video_id else ""

    # Initialize session state with sensible defaults
    st.session_state.setdefault("video_url", reconstructed_url)
    st.session_state.setdefault("allow_youtube_captions", q.get("captions", "true").lower() == "true")
    st.session_state.setdefault("flow_param", q.get("flow", ""))
    st.session_state.setdefault("custom_prompt", q.get("prompt", ""))
    
    # Keep track of previous URL for change detection
    st.session_state.setdefault("old_video_url", st.session_state["video_url"])


def sync_query_params() -> None:
    """
    Synchronize session state back to query parameters.
    
    This function updates URL query parameters based on the current session state,
    ensuring that the URL reflects the current application state for sharing.
    """
    q = st.query_params

    # Extract video ID from the URL and update query parameter
    video_url = st.session_state["video_url"].strip()
    video_id = extract_video_id(video_url)

    if video_id:
        q["vid"] = video_id
    else:
        q.pop("vid", None)

    # Handle caption preference
    if st.session_state["allow_youtube_captions"]:
        q.pop("captions", None) 
    else:
        q["captions"] = "false" 

    # Handle flow selection
    flow_param = st.session_state["flow_param"].strip()
    if flow_param:
        q["flow"] = flow_param
    else:
        q.pop("flow", None)

    # Handle custom prompt (only if custom flow is selected)
    custom_prompt = st.session_state["custom_prompt"].strip()
    if flow_param == "custom" and custom_prompt:
        q["prompt"] = custom_prompt
    else:
        q.pop("prompt", None)


def reset_flow_if_new_url() -> None:
    """
    Reset flow selection when the video URL changes.
    
    This callback function is triggered when the video URL input changes,
    ensuring that the flow selection is reset to avoid confusion when 
    switching between videos.
    """
    old_url = st.session_state.get("old_video_url", "")
    new_url = st.session_state["video_url"].strip()
    
    if new_url != old_url:
        st.session_state["flow_param"] = ""
        st.session_state["old_video_url"] = new_url
        # Clear context flow state when URL changes
        st.session_state.pop("context_claims", None)
        st.session_state.pop("selected_claim_index", None)


def render_header() -> None:
    """Render the app title and header section."""
    st.title("Tube Clues")
    st.markdown(
        """<style>.reportview-container .markdown-text { text-align: center; }</style>""",
        unsafe_allow_html=True
    )

def check_worker_status() -> None:
    # Check if worker is available
    if not worker_alive():
        st.warning("Worker is out for lunch, only previously cached transcripts will work")
        _, cent_co, _ = st.columns(3)
        with cent_co:
            st.image("data/amigo.png", use_column_width=True)


def render_input_controls() -> tuple[bool, bool, bool, bool, bool]:
    """
    Render the input controls section of the UI.
    
    Returns:
        tuple: (clickbait_active, bias_active, custom_active, context_active, any_button_clicked)
    """
    # Video URL input with change callback
    st.text_input(
        "Enter video URL: ",
        placeholder="",
        key="video_url",
        on_change=reset_flow_if_new_url
    )

    # Caption preference checkbox
    st.checkbox(
        "Prefer YouTube Caption Usage",
        help=(
            "Using existing captions from YouTube can be faster if a manually generated "
            "transcript is available and a generated one is not cached in TubeClues."
        ),
        key="allow_youtube_captions"
    )

    # Flow selection buttons
    st.write("Click button for chosen flow: ")
    col1, col2, col3 = st.columns([1, 1, 1], gap="small")
    
    with col1:
        clickbait_button = st.button("Clickbait", use_container_width=True)
    with col2:
        custom_button = st.button("Custom Prompt", use_container_width=True)
    with col3:
        context_button = st.button("Provide Context", use_container_width=True)
    
    bias_button = False  # Disable bias flow

    # Update flow based on button clicks
    if clickbait_button:
        st.session_state["flow_param"] = "clickbait"
    elif custom_button:
        st.session_state["flow_param"] = "custom"
    elif bias_button:
        st.session_state["flow_param"] = "bias"
    elif context_button:
        st.session_state["flow_param"] = "context"

    # Custom prompt input
    st.text_input(
        "Enter custom prompt: ",
        placeholder="What's the recipe?",
        key="custom_prompt"
    )

    # Auto-switch to custom flow if prompt typed (unless another button was just clicked)
    if st.session_state["custom_prompt"].strip() and not (clickbait_button or context_button):
        st.session_state["flow_param"] = "custom"

    # Determine active flow
    flow_param = st.session_state["flow_param"]
    clickbait_active = (flow_param == "clickbait")
    bias_active = (flow_param == "bias")
    custom_active = (flow_param == "custom")
    context_active = (flow_param == "context")
    any_button_clicked = (clickbait_active or bias_active or custom_active or context_active)
    
    return clickbait_active, bias_active, custom_active, context_active, any_button_clicked


def validate_video(video_url: str) -> tuple[bool, str]:
    """
    Validate the video URL and duration.
    
    Args:
        video_url: The URL to validate
        
    Returns:
        tuple: (is_valid, video_id)
            - is_valid: True if video is valid, False otherwise
            - video_id: The extracted video ID if valid, empty string otherwise
    """
    # Extract and validate video ID
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid video URL.")
        return False, ""

    # Validate video length
    duration = get_video_duration(video_id)
    max_duration = datetime.timedelta(minutes=60)
    
    if duration > max_duration:
        st.error(f"Video duration of {duration} is too long. Maximum supported duration is {max_duration}.")
        return False, ""
        
    if duration > datetime.timedelta(minutes=10):
        st.warning("Video duration is over 10 minutes, processing time may be extended.")
        
    return True, video_id


def get_video_transcript(video_id: str) -> tuple[str, float, bool]:
    """
    Retrieve transcript for the video.
    
    Args:
        video_id: The YouTube video ID
        
    Returns:
        tuple: (transcript, elapsed_time, from_captions)
            - transcript: The retrieved transcript text
            - elapsed_time: Time taken to retrieve transcript
            - from_captions: Whether transcript was retrieved from YouTube captions
    """
    start_time = time.time()
    transcript = None
    from_captions = False

    # Try YouTube captions first if enabled
    if st.session_state["allow_youtube_captions"]:
        with st.spinner("Retrieving transcript for video from YouTube..."):
            transcript = get_transcript(video_id, "youtube")
            if transcript:
                from_captions = True

    # Fall back to audio processing if needed
    if not transcript:
        transcript = transcript_creation_flow(video_id)
        
    elapsed_time = time.time() - start_time
    
    return transcript or "", elapsed_time, from_captions


def execute_selected_flow(
    transcript: str, 
    video_id: str, 
    clickbait_active: bool, 
    bias_active: bool, 
    custom_active: bool,
    context_active: bool
) -> float:
    """
    Execute the selected flow based on user choice.
    
    Args:
        transcript: The video transcript
        video_id: The YouTube video ID
        clickbait_active: Whether clickbait flow is active
        bias_active: Whether bias flow is active
        custom_active: Whether custom flow is active
        context_active: Whether context flow is active
        
    Returns:
        float: Time taken to execute the flow
    """
    flow_elapsed_time = 0.0
    
    if clickbait_active:
        flow_elapsed_time = title_flow(transcript, video_id)
    elif bias_active:
        flow_elapsed_time = bias_flow(transcript)
    elif custom_active:
        prompt_text = st.session_state["custom_prompt"].strip()
        if 1 <= len(prompt_text) <= 250:
            flow_elapsed_time = custom_flow(prompt_text, transcript)
        else:
            st.error("Custom prompt must be between 1 and 250 characters.")
    elif context_active:
        flow_elapsed_time = context_flow(transcript)
            
    return flow_elapsed_time


def main():
    """Main application entry point."""
    logging.info("Starting Tube Clues...")
    init_query_params()
    
    render_header()
    check_worker_status()
    
    # Render input controls and get selected flow
    clickbait_active, bias_active, custom_active, context_active, any_button_clicked = render_input_controls()
    
    # Get and validate video URL
    video_url = st.session_state["video_url"].strip()
    if not video_url and not any_button_clicked:
        sync_query_params()
        return

    # Validate custom flow has a prompt
    if custom_active and not st.session_state["custom_prompt"].strip():
        st.error("A prompt is required for the question answering flow.")
        sync_query_params()
        return

    # Validate video
    is_valid, video_id = validate_video(video_url)
    if not is_valid:
        sync_query_params()
        return
        
    # Get transcript
    transcript, transcript_elapsed_time, from_captions = get_video_transcript(video_id)
    if not transcript:
        st.error("Transcript creation failed.")
        sync_query_params()
        return
        
    # Display timing information
    st.sidebar.info(f"Transcript retrieved in {transcript_elapsed_time:.2f} seconds.")
    
    # Display transcript
    transcript_title = (
        "Video Transcript (Retrieved From YouTube)" if from_captions
        else "Video Transcript (Generated from Video Audio)"
    )
    with st.expander(transcript_title, expanded=False):
        st.write(escape_all_markdown(transcript))
        
    # Execute selected flow
    flow_elapsed_time = execute_selected_flow(
        transcript, video_id, clickbait_active, bias_active, custom_active, context_active
    )
    
    # Display timing information
    st.sidebar.info(f"Answer crafted in {flow_elapsed_time:.2f} seconds.")
    total_time = flow_elapsed_time + transcript_elapsed_time
    st.sidebar.info(f"The total flow took {total_time:.2f} seconds.")
    
    if not any_button_clicked:
        st.info("For additional processing, please select an option above.")
        
    # Sync final state
    sync_query_params()

if __name__ == '__main__':
    main()
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)
