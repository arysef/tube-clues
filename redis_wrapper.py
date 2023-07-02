import datetime
import os
import redis 
# from redis_lock import Lock
from typing import Optional



AZURE_REDIS_HOST = os.environ.get("AZURE_REDIS_HOST")
AZURE_REDIS_KEY = os.environ.get("AZURE_REDIS_KEY")
DEFAULT_EXPIRATION = datetime.timedelta(days=30)
DEFAULT_LOCK_TIMEOUT = 120

transcript_cache = redis.StrictRedis(host=AZURE_REDIS_HOST, port=6380,
                      password=AZURE_REDIS_KEY, ssl=True, decode_responses=True, db=0)
transcript_locks = transcript_cache = redis.StrictRedis(host=AZURE_REDIS_HOST, port=6380,
                      password=AZURE_REDIS_KEY, ssl=True, decode_responses=True, db=1)
gpt_response_cache = transcript_cache = redis.StrictRedis(host=AZURE_REDIS_HOST, port=6380,
                      password=AZURE_REDIS_KEY, ssl=True, decode_responses=True, db=2)



def test():
    result = transcript_cache.ping()
    print("Ping returned : " + str(result))

    result = transcript_cache.setex("Message", DEFAULT_EXPIRATION, "Hello!, The cache is working with Python!")
    print("SET Message returned : " + str(result))

    result = transcript_cache.get("Message")
    print("GET Message returned : " + result)
    return 0

def get_cached_transcript(video_id:str) -> Optional[str]: 
    return transcript_cache.get(video_id)

def set_cached_transcript(video_id:str, transcript:str) -> None: 
    transcript_cache.setex(video_id, DEFAULT_EXPIRATION, transcript)

def get_cached_gpt_response(query:str ) -> Optional[str]:
    return gpt_response_cache.get(query)

def set_cached_gpt_response(query:str, response:str) -> None:
    gpt_response_cache.setex(query, DEFAULT_EXPIRATION, response)

def lock_transcript(video_id:str, blocking=True) -> Optional[redis.lock.Lock]:
    # Acquire lock for the video ID, timeout after DEFAULT_LOCK_TIMEOUT
    lock = transcript_locks.lock(video_id, timeout=DEFAULT_LOCK_TIMEOUT, blocking_timeout=DEFAULT_LOCK_TIMEOUT)
    acquired = lock.acquire(blocking=blocking)
    if acquired: 
        return lock
    return None

def release_transcript_lock(lock: Optional[redis.lock.Lock]) -> None:
    if lock:
        lock.release()
