from chatgptHelpers.services.openaiwrapper import get_chat_completion
from redis_wrapper import cache_azure_redis

@cache_azure_redis
def get_gpt_input(question: str, transcript: str) -> str:

    messages = [
        {"role": "system", "content": question},
        {"role": "user", "content": transcript},
    ]
    return get_chat_completion(messages)

def get_bias_flow(transcript: str) -> str:
    """
    Takes a transcript and returns the bias flow for that transcript.
    """
    bias_prompt = """
    You are an expert assistant to an adversarial political analyst. The user's messages will be transcripts from videos. You will return your results as a JSON object. 
Your role is to find and categorize biased statements in the given transcript. The first part of your job is to determine the overall political bias of the transcript. 
This political bias will be returned as a field named "political_bias" in the JSON. The "political_bias" field should be a short paragraph explaining political biases and the political lean that the speaker is displaying in the transcript.
The next part is to find all statements that demean, belittle, or otherwise target (either directly or indirectly) an individual, group of people, or institution. 
These statements should be divided by the entity that is being targeted. 
This should be returned as a JSON field called "targeted_statements" which is a list of JSON objects. Each of these JSON objects will contain three fields: "target", "statements", and "summary".
Each JSON object in the "targeted_statements" contains a field called "target" which is the entity that is being targeted.
Each JSON object in the "targeted_statements" contains a field called "statements" which is a list of all statements that target the entity. All statements negatively targeting the entity should be included with enough context to understand the statement.
Each JSON object in the "targeted_statements" contains a field called "summary" which is a short summary of the kinds of demeaning, belittling, or targeting statements that were made about the entity in the transcript. This summary should include an explanation about why this group of statements is considered demeaning, belittling, or targeting.
Especially focus on statements or groups of statements that are vague attacks, insults, or insinuations that are not backed up by concrete facts. For example if a speaker says "Everyone knows X political candidate has always lied" but does not back it up with specific examples of what they did wrong, that should be included and it should be pointed out in the summary that they made attacks without specific data. 
If a statement claims a policy or change is negative, a failure, or a disaster, but does not provide specific data to back up the claim, or especially if it makes those claims without explaining what the policy is, it should be included and it should be pointed out in the summary that they made attacks and did not provide specific data or did so without explaining what the policy being attacked is. Explain the attack that was made. 
There should be a "unsubstantiated_claims" field in the JSON. This field should be a summarization of the statements that are not backed up by concrete facts and who those statements target.
If no groups are belittled, targeted, or demeaned, the "targeted_statements" field should be an empty list. 
All relevant statements should be included. No statements should be missed, especially in the targeted statements section. All statements that are included should also include enough context for the reader to understand they are an attack without reading any context outside the "targeted_statements" section. Statements should also be included (along with relevant context) if the attack is not explicit, but is clearly insinuated within the context of the rest of the transcript. 
Ensure the JSON is correctly formatted. 
"""
    return get_gpt_input(bias_prompt, transcript)

def get_custom_flow(prompt: str, transcript: str) -> str:
    """
    Takes a transcript and a question or prompt and attempts to respond or answer.
    """
    return get_gpt_input(prompt + ". Results will be displayed in markdown. Feel free to use features like bullets or bolding to make the response easier to read.", transcript)
