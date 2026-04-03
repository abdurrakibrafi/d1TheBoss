# config/celery.py
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


from celery.schedules import crontab
 
CELERY_BEAT_SCHEDULE = {
    # Every Sunday at 00:00 UTC — close last week (mark missed)
    'close-week-saturday-midnight': {
        'task': 'checkin.close_week_on_saturday',
        'schedule': crontab(hour=0, minute=0, day_of_week='sunday'),
    },
    # Every Sunday at 00:01 UTC — open new week for all users
    'create-weekly-checkins-sunday': {
        'task': 'checkin.create_weekly_checkins_for_all_users',
        'schedule': crontab(hour=0, minute=1, day_of_week='sunday'),
    },
}
 