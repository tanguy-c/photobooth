# flake8: noqa
from photobooth.settings.base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "photobooth",
        "USER": "photobooth_user",
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD", 'password'),
        "HOST": "postgresql",
        "PORT": "",
    }
}

CELERY_BROKER_URL = 'amqp://rabbitmq'
