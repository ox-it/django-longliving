import logging
import os
import sys
import threading
import time
import traceback

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

from django_longliving.base import LonglivingThread
from django_longliving.util import get_redis_client

logger = logging.getLogger(__name__)

class ThreadRunner(object):
    LOCK_NAME = 'django-longliving:lock'

    def __init__(self):
        self.bail = threading.Event()

    def get_threads(self):
        try:
            longliving_classes = set(settings.LONGLIVING_CLASSES)
        except AttributeError:
            raise ImproperlyConfigured("LONGLIVING_CLASSES setting missing.")
        longliving_classes.add('django_longliving.longliving.stop_watcher.StopWatcherThread')

        threads = []
        for class_path in longliving_classes:
            module_name, class_name = class_path.rsplit('.', 1)
            try:
                module = import_module(module_name)
            except ImportError:
                raise ImproperlyConfigured("Could not import module %r" % module_name)
            try:
                cls = getattr(module, class_name)
            except AttributeError:
                raise ImproperlyConfigured("Module %r has no attribute %r" % (module_name, class_name))
            if not issubclass(cls, threading.Thread):
                raise ImproperlyConfigured("%r must be a subclass of threading.Thread" % class_path)
            thread = threading.Thread(target=self.thread_container,
                                      args=(class_path, cls),
                                      name=class_path)
            threads.append(thread)
        return threads

    def thread_container(self, class_path, cls):
        restart_delay = 1

        while True:
            started = time.time()
            thread = cls(self.bail)
            logger.info("Starting thread: %s", class_path)
            try:
                thread.run()
            except Exception:
                restart_delay -= (time.time() - started) / 10
                restart_delay = min(max(1, restart_delay * 2), 7200) # back off exponentially, with outer bounds of 1 second and two hours.
                logger.exception("Thread exited abnormally: %s, restarting in %.2f seconds", class_path, restart_delay)
                time.sleep(restart_delay)
            else:
                if self.bail.isSet():
                    logger.info("Thread exited normally: %s", class_path)
                else:
                    logger.warning("Thread exited normally, but probably shouldn't have: %s", class_path)
                break

    def stop(self, signo=None, frame=None):
        self.bail.set()
        redis_client = get_redis_client()
        redis_client.publish(LonglivingThread.BAIL_CHANNEL, '')


    def run(self):
        redis_client = get_redis_client()

        existing_pid = redis_client.get(self.LOCK_NAME)
        if not redis_client.setnx(self.LOCK_NAME, os.getpid()):
            existing_pid = int(redis_client.get(self.LOCK_NAME))
            try:
                os.kill(existing_pid, 0)
            except OSError:
                redis_client.set(self.LOCK_NAME, os.getpid())
            else:
                logger.warning("Not starting as another instance detected.")
                sys.stderr.write("Already running\n")
                sys.exit(1)
        logger.info("Starting longliving process")

        try:
            threads = self.get_threads()

            for thread in threads:
                thread.start()

            logger.info("Longliving threads started")

            try:
                while not self.bail.isSet():
                    time.sleep(1)
                logger.info("Shutting down")
            except KeyboardInterrupt:
                logger.info("Caught KeyboardInterrupt; shutting down.")
                self.bail.set()
                redis_client.publish(LonglivingThread.BAIL_CHANNEL, '')

            for i in range(5):
                for thread in threads[:]:
                    thread.join(5)
                    if thread.isAlive():
                        frame = sys._current_frames()[thread.ident]
                        try:
                            logger.warning("Couldn't join thread %r on attempt %i/5:\n%s", thread.name, i + 1, ''.join(traceback.format_stack(frame)))
                        finally:
                            del frame
                    else:
                        threads.remove(thread)

            if threads:
                logger.error("Couldn't join all threads.")
            else:
                logger.info("All threads finished; stopping.")
        finally:
            redis_client.delete(self.LOCK_NAME)
