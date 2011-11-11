import inspect

from django.core.exceptions import ImproperlyConfigured

_allowable_args = frozenset(['channel', 'data', 'client'])

def pubsub_watcher(channel=None, channels=None, priority=0):
    if not (channel or channels):
        raise ImproperlyConfigured("Must supply one or other of key and keys")
    channels = channels or ()
    if channel:
        channels += (channel,)

    def decorator(f):
        argspec = inspect.getargspec(f)
        args = set(argspec[0])
        if args - _allowable_args:
            raise ImproperlyConfigured("Callable has wrong argspec (should be some subset of {%s})" % ', '.join(_allowable_args))
        f._pubsub_watcher_meta = PubSubWatcherMeta(channels=channels, priority=priority, args=args)

        return f
    return decorator

class PubSubWatcherMeta(object):
    def __init__(self, channels, priority, args):
        self.channels = frozenset(channels)
        self.priority = priority
        self.args = args
