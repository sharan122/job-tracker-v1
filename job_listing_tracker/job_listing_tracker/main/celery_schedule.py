from celery.schedules import crontab
from celery_app import celery_app, run_script

# Celery Beat Configuration (Twice a day at 12 AM and 12 PM)
celery_app.conf.beat_schedule = {
    'run-my-script-twice-daily': {
        'task': 'celery_app.run_script',
        'schedule': crontab(hour="0,12", minute=0),
    },
}
celery_app.conf.timezone = 'UTC'

if __name__ == "__main__":
    run_script.delay()  # Run task immediately if needed
