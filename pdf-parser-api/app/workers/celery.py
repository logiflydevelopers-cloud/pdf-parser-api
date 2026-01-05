from celery import Celery
import os

celery = Celery(
    "worker",
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"]
)

celery.autodiscover_tasks(["app.workers"])
