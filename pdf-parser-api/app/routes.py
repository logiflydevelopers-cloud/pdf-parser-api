from fastapi import APIRouter, HTTPException
from app.repos.redis_jobs import get_job_repo
from app.repos.firestore_repo import FirestoreRepo
from app.workers.ingest_task import ingest_pdf as ingest_pdf_task
from app.schemas.ingest import IngestRequest
from app.schemas.qa import AskRequest
from app.services.qa_engine import answer_question
import os

USE_CELERY = os.getenv("USE_CELERY", "true").lower() == "true"

router = APIRouter(prefix="/v1")

jobs = get_job_repo()
store = FirestoreRepo()


# --------------------------------------------------
# Ingest PDF
# --------------------------------------------------
@router.post("/pdfs/ingest", status_code=202)
def ingest(req: IngestRequest):
    job = jobs.create(req.pdfId)

    if USE_CELERY:
        # Production (Render + Celery)
        ingest_pdf_task.delay(
            job["jobId"],
            req.userId,
            req.pdfId,
            req.source.dict()
        )
    else:
        # Local dev (no Celery)
        ingest_pdf_task(
            job["jobId"],
            req.userId,
            req.pdfId,
            req.source.dict()
        )

    return {
        "jobId": job["jobId"],
        "pdfId": req.pdfId,
        "status": "queued"
    }


# --------------------------------------------------
# Job status
# --------------------------------------------------
@router.get("/jobs/{jobId}")
def job_status(jobId: str):
    data = jobs.get(jobId)

    if data["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")

    if data["status"] == "done":
        data["result"] = store.get(data["pdfId"])

    return data


# --------------------------------------------------
# Ask question (RAG)
# --------------------------------------------------
@router.post("/pdfs/{pdfId}/ask")
def ask(pdfId: str, req: AskRequest):
    data = store.get(pdfId)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="PDF not processed or not found"
        )

    answer, mode, sources = answer_question(
        summary=data["summary"],
        question=req.question,
        pdfId=pdfId
    )

    return {
        "pdfId": pdfId,
        "question": req.question,
        "answer": answer,
        "answerMode": mode,
        "sources": sources
    }
