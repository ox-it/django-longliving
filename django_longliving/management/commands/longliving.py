import logging
from optparse import make_option
import signal
import sys

from django.core.management.base import BaseCommand

from django_longliving.runner import ThreadRunner


class Command(BaseCommand):
    LOCK_NAME = 'django-longliving:lock'

    option_list = BaseCommand.option_list + (
        make_option('--log-level',
            action='store',
            dest='loglevel',
            default=None,
            help='Log level'),
        make_option('--log-file',
            action='store',
            dest='logfile',
            default=None,
            help='Log destination')
        )

    def sigterm(self, signo, frame):
        self.bail.set()

    def configure_logging(self, **options):
        log_level = options.pop('loglevel', None)
        if not log_level:
            return
        stream = options.pop('logstream', None) or sys.stderr
        if isinstance(stream, basestring):
            stream = open(stream, 'a')
        logging.basicConfig(stream=stream,
                            level=getattr(logging, log_level.upper()))

    def handle(self, *args, **options):
        self.configure_logging(**options)

        runner = ThreadRunner()
        signal.signal(signal.SIGINT, runner.stop)
        signal.signal(signal.SIGTERM, runner.stop)
        runner.run()
