import datetime
from functools import wraps
import os
import redis 
from typing import Optional

AZURE_REDIS_HOST = os.environ.get("AZURE_REDIS_HOST")
AZURE_REDIS_KEY = os.environ.get("AZURE_REDIS_KEY")
DEFAULT_EXPIRATION = datetime.timedelta(days=30)
DEFAULT_LOCK_TIMEOUT = 120

value_cache = redis.StrictRedis(host=AZURE_REDIS_HOST, port=6380,
                      password=AZURE_REDIS_KEY, ssl=True, decode_responses=True, db=0)
lock_cache = redis.StrictRedis(host=AZURE_REDIS_HOST, port=6380,
                      password=AZURE_REDIS_KEY, ssl=True, decode_responses=True, db=1)

def cache_azure_redis(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a cache key based on the function's name and its arguments
        key = f'{func.__name__}:{str(args)}:{str(kwargs)}'
        # Try to get the result from cache
        result = value_cache.get(key)
        if result is not None:
            print("Cache hit")
            # If a result is found in the cache, return it
            return result
        else:
            print("Cache miss")
            # If no result is found in cache, we need to compute it.
            # Before computing, lock the key to prevent other function calls from computing the same value
            lock = lock_cache.lock(key, timeout=DEFAULT_LOCK_TIMEOUT, blocking_timeout=DEFAULT_LOCK_TIMEOUT)
            lock.acquire(blocking=True)
            try:
                # Check the cache again, to avoid a race condition where the value might have been computed by another process
                result = value_cache.get(key)
                if result is not None:
                    print("Cache hit after waiting for lock")
                    return result
                else:
                    # Compute the result and cache it
                    print("Computing result")
                    result = func(*args, **kwargs)
                    value_cache.setex(key, DEFAULT_EXPIRATION, result)  # Assuming the result is already a string
                    return result
            finally:
                # Always make sure to release the lock, even if an error occurred while computing the function
                lock.release()
    return wrapper

def stream_cache_azure_redis(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = f'{func.__name__}:{str(args)}:{str(kwargs)}'
        
        # Try to get the result from cache
        cached_result = value_cache.get(key)
        if cached_result is not None:
            print("Cache hit")
            yield cached_result
            return
        else:
            print("Cache miss")
            # Acquire lock before computing
            lock = lock_cache.lock(key, timeout=DEFAULT_LOCK_TIMEOUT, blocking_timeout=DEFAULT_LOCK_TIMEOUT)
            lock.acquire(blocking=True)
            try:
                # Double-check the cache after acquiring the lock
                cached_result = value_cache.get(key)
                if cached_result is not None:
                    print("Cache hit after waiting for lock")
                    yield cached_result
                else:
                    print("Computing result")
                    last_result = None
                    for result in func(*args, **kwargs):
                        last_result = result
                        yield result
                    # Cache the final result
                    if last_result is not None:
                        last_result = ''.join(last_result)
                        print("Caching streamed result")
                        value_cache.setex(key, DEFAULT_EXPIRATION, last_result)
            finally:
                # Always release the lock
                lock.release()

    return wrapper