from celery import Celery
import os

celery = Celery(
    "worker",
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
)

# FORCE IMPORT OF TASKS
import app.workers.ingest_task
