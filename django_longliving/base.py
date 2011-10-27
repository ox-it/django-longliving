import threading

import redis

from django.conf import settings

from . import util

class LonglivingThread(threading.Thread):
    BAIL_CHANNEL = 'django-longliving:bail'

    def __init__(self, bail):
        self._bail = bail
        super(LonglivingThread, self).__init__()
    def get_redis_client(self):
        return redis.client.Redis(**settings.REDIS_PARAMS)
    def watch_queue(self, client, name, unpack=False):
        while not self._bail.isSet():
            result = client.blpop(name, 2)
            if not result:
                continue
            key, item = result
            if unpack:
                item = self.unpack(item)

            yield key, item

    pack = staticmethod(util.pack)
    unpack = staticmethod(util.unpack)
