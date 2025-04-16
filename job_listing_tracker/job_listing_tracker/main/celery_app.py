from celery import Celery
import subprocess  # To run the script

# Configure Celery
celery_app = Celery(
    'my_task',
    broker='redis://localhost:6379/0',  # Redis as message broker
    backend='redis://localhost:6379/0'  # Optional, for result storage
)

@celery_app.task
def run_script():
    """Task to run the Python script."""
    try:
        subprocess.run(["python3", "job_listing_tracker\main\main.py"], check=True)
        return "Script executed successfully"
    except subprocess.CalledProcessError as e:
        return f"Script failed: {e}"

