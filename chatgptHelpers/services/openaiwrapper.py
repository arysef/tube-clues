from typing import Generator, List
import openai
import os

from tenacity import retry, wait_random_exponential, stop_after_attempt
from time import time
OPENAI_EMBEDDING_ENGINE = os.environ.get("OPENAI_EMBEDDING_ENGINE")
OPENAI_CHAT_ENGINE = "gpt-4o"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

assert OPENAI_EMBEDDING_ENGINE is not None
assert OPENAI_CHAT_ENGINE is not None
assert OPENAI_API_KEY is not None
openai.api_key = OPENAI_API_KEY


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_embeddings(texts: List[str], model=OPENAI_EMBEDDING_ENGINE) -> List[List[float]]:
    """
    Embed texts using OpenAI's ada model.

    Args:
        texts: The list of texts to embed.

    Returns:
        A list of embeddings, each of which is a list of floats.

    Raises:
        Exception: If the OpenAI API call fails.
    """
    # Call the OpenAI API to get the embeddings
    response = openai.Embedding.create(input=texts, engine=model)

    # Extract the embedding data from the response
    data = response["data"]  # type: ignore

    # Return the embeddings as a list of lists of floats
    return [result["embedding"] for result in data]


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_chat_completion(
    messages,
    json=False
) -> str:
    """
    Generate a chat completion using OpenAI's chat completion API.

    Args:
        messages: The list of messages in the chat history.
        model: The name of the model to use for the completion. Default is gpt-3.5-turbo, which is a fast, cheap and versatile model. Use gpt-4 for higher quality but slower results.

    Returns:
        A string containing the chat completion.

    Raises:
        Exception: If the OpenAI API call fails.
    """
    # call the OpenAI chat completion API with the given messages
    
    print("Starting chat completion...")
    start_time = time()
    response = openai.ChatCompletion.create(
        model=OPENAI_CHAT_ENGINE,
        messages=messages,
        stream=False,
        response_format= { "type": "json_object" } if json else None
    )
    end_time = time()
    print(f"Chat completion finished in {end_time-start_time:.2f} seconds.")

    choices = response["choices"]  # type: ignore
    completion = choices[0].message.content.strip()
    return completion.replace("$", "\\\\$")

def streaming_get_chat_completion(messages: str) -> Generator[str, None, None]:
    response = openai.ChatCompletion.create(
        model=OPENAI_CHAT_ENGINE,
        messages=messages,
        stream=True,
    )

    completion_text = ''
    for event in response:
        if 'content' in event['choices'][0]['delta']:
            event_text = event['choices'][0]['delta']['content']
            event_text = event_text.replace("$", "\\$")
            completion_text += event_text
            yield completion_text

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def get_whisper_transcript(file_path, model="whisper-1"):
    """
    Generate a transcript using OpenAI's Whisper transcript API.

    Args: 
        file_path: The file path of the mp3 being passed in.
        model: The model to use. As of this comment, only whisper-1 is available on OpenAI endpoint.

    Raises: 
        Exception if OpenAI API call fails.
    """
    audio_file = open(file_path, "rb")
    
    print("Starting transcription...")
    start_time = time()
    transcript = openai.Audio.transcribe(model, audio_file, response_format="text")
    end_time = time()
    print(f"Transcription completed in {end_time-start_time:.2f} seconds.")
    
    return transcript

