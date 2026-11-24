import redis
from app.config import REDIS_URL, REDIS_STREAM, REDIS_GROUP

def get_redis():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=3)

def ensure_group(client):
    try:
        client.xgroup_create(REDIS_STREAM, REDIS_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
