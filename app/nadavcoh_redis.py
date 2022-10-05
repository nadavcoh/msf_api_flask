import sys
from datetime import timedelta
import redis
import json
from flask import current_app, g

def redis_connect() -> redis.client.Redis:
    try:
        client = redis.Redis(
            host="localhost",
            port=6379,
#            password="ubuntu",
            db=0,
            socket_timeout=5,
        )
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        print("AuthenticationError")
        sys.exit(1)

def get_redis():
    if 'redis' not in g:
        g.redis = redis_connect()
    return g.redis

def close_redis(e=None):
    redis = g.pop('redis', None)

    if redis is not None:
        redis.close()

def init_app(app):
    app.teardown_appcontext(close_redis)

def check_hash():
    redis_client = get_redis()
    cache_hash = redis_client.get("char_hash").decode()
    if cache_hash != current_chars_hash:
        print("Hash mismathch: %s %s", (cache_hash, current_chars_hash))
        redis_client.flushdb()
        redis_client.set("char_hash", current_chars_hash)

def get_data_from_cache(key: str) -> str:
    """Data from redis."""
    redis_client = get_redis()
    val = redis_client.get(key)
    if val is not None:
        val = json.loads(val)
        val["cache"] = True
        return val
    else:
        return (val)

def set_data_to_cache(key: str, value: str) -> bool:
    """Data to redis."""
    redis_client = get_redis()
    state = redis_client.set(key, value=json.dumps(value))
    return state
