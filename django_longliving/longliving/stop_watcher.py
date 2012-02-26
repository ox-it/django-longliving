from django_longliving.base import LonglivingThread

class StopWatcherThread(LonglivingThread):
    STOP_CHANNEL = 'django-longliving:stop-channel'

    def run(self):
        client = self.get_redis_client()

        pubsub = client.pubsub()
        pubsub.subscribe(StopWatcherThread.STOP_CHANNEL)
        pubsub.subscribe(LonglivingThread.BAIL_CHANNEL)
        try:
            for message in pubsub.listen():
                if self._bail.isSet():
                    break
                if message['channel'] == StopWatcherThread.STOP_CHANNEL:
                    self._bail.set()
                    client.publish(LonglivingThread.BAIL_CHANNEL, '')
                    break
        finally:
            pubsub.unsubscribe(StopWatcherThread.STOP_CHANNEL)
            pubsub.unsubscribe(LonglivingThread.BAIL_CHANNEL)

