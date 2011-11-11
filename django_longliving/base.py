import threading

from . import util

class LonglivingThread(threading.Thread):
    BAIL_CHANNEL = 'django-longliving:bail'

    def __init__(self, bail):
        self._bail = bail
        super(LonglivingThread, self).__init__()
    def watch_queue(self, client, name, unpack=False):
        while not self._bail.isSet():
            result = client.blpop(name, 2)
            if not result:
                continue
            key, item = result
            if unpack:
                item = self.unpack(item)

            yield key, item

    get_redis_client = staticmethod(util.get_redis_client)
    pack = staticmethod(util.pack)
    unpack = staticmethod(util.unpack)
