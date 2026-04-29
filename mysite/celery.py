import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Name your Celery app
app = Celery('mysite')

# Tell Celery to read config variables from Django's settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tell Celery to automatically find any 'tasks.py' files in your apps
app.autodiscover_tasks()