from fastapi import APIRouter
from app.repos.redis_jobs import get_job_repo
from app.repos.firestore_repo import FirestoreRepo
from app.workers.ingest_task import ingest_pdf
from app.schemas.ingest import IngestRequest
from app.schemas.qa import AskRequest
from app.services.qa_engine import answer_question

import os
USE_CELERY = os.getenv("USE_CELERY", "true").lower() == "true"


router = APIRouter()
jobs = get_job_repo()
store = FirestoreRepo()

@router.post("/pdfs/ingest", status_code=202)
def ingest(req: IngestRequest):
    job = jobs.create(req.pdfId)

    if USE_CELERY:
        # Production (Render)
        ingest_pdf.delay(job["jobId"], req.pdfId, req.source.dict())
    else:
        # Local dev (NO Redis, NO Celery)
        from app.workers.ingest_task import ingest_pdf
        ingest_pdf(
            job["jobId"],
            req.pdfId,
            req.source.dict()
        )

    return job


@router.get("/jobs/{jobId}")
def job(jobId: str):
    data = jobs.get(jobId)
    if data["status"] == "done":
        data["result"] = store.get(data["pdfId"])
    return data

@router.post("/pdfs/{pdfId}/ask")
def ask(pdfId: str, req: AskRequest):
    data = store.get(pdfId)
    answer, mode, sources = answer_question(
        data["summary"], req.question, pdfId
    )
    return {
        "pdfId": pdfId,
        "question": req.question,
        "answer": answer,
        "answerMode": mode,
        "sources": sources
    }
