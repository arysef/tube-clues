import datetime
import logging
import os
from functools import wraps
from typing import Optional

import redis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

AZURE_REDIS_HOST = os.environ.get("AZURE_REDIS_HOST")
AZURE_REDIS_KEY = os.environ.get("AZURE_REDIS_KEY")
DEFAULT_EXPIRATION = datetime.timedelta(days=30)
DEFAULT_LOCK_TIMEOUT = 120
QUEUE_NAME = "transcript_queue"

value_cache = redis.StrictRedis(
    host=AZURE_REDIS_HOST, 
    port=6380,
    password=AZURE_REDIS_KEY, 
    ssl=True, 
    decode_responses=True, 
    db=0
)

lock_cache = redis.StrictRedis(
    host=AZURE_REDIS_HOST, 
    port=6380,
    password=AZURE_REDIS_KEY, 
    ssl=True, 
    decode_responses=True, 
    db=1
)

def cache_azure_redis(func):
    """
    A decorator that caches the return value of a function in Azure Redis.
    Utilizes a lock in db=1 to avoid race conditions when multiple processes
    call the same function concurrently.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = f"{func.__name__}:{args}:{kwargs}"
        result = value_cache.get(key)

        if result is not None:
            logging.info(f"[cache_azure_redis] Cache hit for key: {key}")
            return result

        logging.info(f"[cache_azure_redis] Cache miss for key: {key}")
        lock = lock_cache.lock(key, timeout=DEFAULT_LOCK_TIMEOUT, blocking_timeout=DEFAULT_LOCK_TIMEOUT)
        
        acquired = lock.acquire(blocking=True)
        if not acquired:
            # If we fail to acquire the lock, either raise or return None
            logging.error(f"Could not acquire lock for key: {key}")
            return None
        
        try:
            # Check cache again inside the lock to avoid race conditions
            result = value_cache.get(key)
            if result is not None:
                logging.info(f"[cache_azure_redis] Cache hit after waiting for lock: {key}")
                return result

            # Compute the result
            logging.info(f"[cache_azure_redis] Computing result for key: {key}")
            result = func(*args, **kwargs)

            # Cache the result if it's non-empty
            if result:
                value_cache.setex(key, DEFAULT_EXPIRATION, result)
            
            return result
        finally:
            if lock.locked():
                lock.release()

    return wrapper

def stream_cache_azure_redis(func):
    """
    A decorator for caching streaming outputs in Azure Redis. 
    This is typically useful if the function yields partial results
    but we also want to store the final result in cache.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = f"{func.__name__}:{args}:{kwargs}"

        cached_result = value_cache.get(key)
        if cached_result is not None:
            logging.info(f"[stream_cache_azure_redis] Cache hit for key: {key}")
            # The entire result is cached; yield it once and return
            yield cached_result
            return

        logging.info(f"[stream_cache_azure_redis] Cache miss for key: {key}")
        lock = lock_cache.lock(key, timeout=DEFAULT_LOCK_TIMEOUT, blocking_timeout=DEFAULT_LOCK_TIMEOUT)
        
        acquired = lock.acquire(blocking=True)
        if not acquired:
            logging.error(f"Could not acquire lock for key: {key}")
            return

        try:
            # Double-check the cache inside the lock
            cached_result = value_cache.get(key)
            if cached_result is not None:
                logging.info(f"[stream_cache_azure_redis] Cache hit after waiting for lock: {key}")
                yield cached_result
                return

            logging.info(f"[stream_cache_azure_redis] Computing streamed result for key: {key}")
            last_result = None

            for partial in func(*args, **kwargs):
                last_result = partial
                yield partial

            # Cache the final result if present
            if last_result is not None:
                # Ensure we have a string-like object to store
                final_str = "".join(last_result) if isinstance(last_result, list) else str(last_result)
                logging.info(f"[stream_cache_azure_redis] Caching streamed result for key: {key}")
                value_cache.setex(key, DEFAULT_EXPIRATION, final_str)
        finally:
            if lock.locked():
                lock.release()

    return wrapper
