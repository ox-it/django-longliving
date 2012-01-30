import logging

import redis

from django.core.management.base import BaseCommand
from django.conf import settings

from django_longliving.longliving.stop_watcher import StopWatcherThread

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        redis_client = redis.client.Redis(**settings.REDIS_PARAMS)
        redis_client.publish(StopWatcherThread.STOP_CHANNEL, '')
