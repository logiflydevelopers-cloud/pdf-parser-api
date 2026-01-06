import json
import uuid
import os
from datetime import datetime


# -------------------------------------------------
# In-memory fallback (LOCAL ONLY)
# -------------------------------------------------
_IN_MEMORY_JOBS = {}


class InMemoryJobRepo:
    def create(self, pdfId: str):
        jobId = f"job_{uuid.uuid4().hex[:8]}"
        data = {
            "jobId": jobId,
            "pdfId": pdfId,
            "status": "queued",
            "stage": "queued",
            "progress": 0,
            "createdAt": datetime.utcnow().isoformat(),
        }
        _IN_MEMORY_JOBS[jobId] = data
        return data

    def update(self, jobId, **kwargs):
        if jobId in _IN_MEMORY_JOBS:
            _IN_MEMORY_JOBS[jobId].update(kwargs)

    def complete(self, jobId):
        self.update(jobId, status="done", progress=100, stage="done")

    def fail(self, jobId, error):
        self.update(jobId, status="failed", error=error)

    def get(self, jobId):
        return _IN_MEMORY_JOBS.get(jobId, {
            "jobId": jobId,
            "status": "not_found"
        })


# -------------------------------------------------
# Redis-backed repo (PRODUCTION + CELERY)
# -------------------------------------------------
class RedisJobRepo:
    def __init__(self):
        import redis
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            raise RuntimeError("REDIS_URL missing")
        self.client = redis.from_url(redis_url, decode_responses=True)

    def create(self, pdfId: str):
        jobId = f"job_{uuid.uuid4().hex[:8]}"
        data = {
            "jobId": jobId,
            "pdfId": pdfId,
            "status": "queued",
            "stage": "queued",
            "progress": 0,
            "createdAt": datetime.utcnow().isoformat(),
        }
        self.client.set(jobId, json.dumps(data))
        return data

    def update(self, jobId, **kwargs):
        raw = self.client.get(jobId)
        if not raw:
            return
        data = json.loads(raw)
        data.update(kwargs)
        self.client.set(jobId, json.dumps(data))

    def complete(self, jobId):
        self.update(jobId, status="done", progress=100, stage="done")

    def fail(self, jobId, error):
        self.update(jobId, status="failed", error=error)

    def get(self, jobId):
        raw = self.client.get(jobId)
        return json.loads(raw) if raw else {
            "jobId": jobId,
            "status": "not_found"
        }


# -------------------------------------------------
# FACTORY (FIXED)
# -------------------------------------------------
def get_job_repo():
    """
    If REDIS_URL exists → ALWAYS Redis
    """
    if os.getenv("REDIS_URL"):
        return RedisJobRepo()
    return InMemoryJobRepo()
