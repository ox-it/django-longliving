import base64
import pickle

from django.conf import settings
import redis

def get_redis_client():
    return redis.client.Redis(**settings.REDIS_PARAMS)
def pack(value):
    return base64.b64encode(pickle.dumps(value))
def unpack(value):
    return pickle.loads(base64.b64decode(value))
