DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}

INSTALLED_APPS = (
    'django_longliving',
)

REDIS_PARAMS = {}

LONGLIVING_CLASSES = set([
    'django_longliving.longliving.pubsub.PubSubDispatcherThread',
    'django_longliving.longliving.stop_watcher.StopWatcherThread',
])
