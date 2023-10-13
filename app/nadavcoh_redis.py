import sys
from datetime import timedelta
import redis
import json
from flask import current_app, g

def redis_connect() -> redis.client.Redis:
    try:
        client = redis.Redis(
            host=current_app.config["REDIS_HOST"],
            port=current_app.config["REDIS_PORT"],
            # host="localhost",
#            host="containers-us-west-202.railway.app",
#            host="red-cg6de5g2qv28u2p72rkg",
#            port=6379,
#            port = 5851,
 #           port = 6379,
            #password="CSHnFW1AuBRot6MZTyJQ",
            db=0,
            socket_timeout=5,
        )
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        current_app.logger.info("AuthenticationError")
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
