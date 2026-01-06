from app.workers.celery import celery
from app.services.pdf_downloader import download_pdf
from app.services.pdf_extractor import extract_pages
from app.services.summarizer import summarize
from app.services.embeddings import build_embeddings
from app.repos.redis_jobs import get_job_repo
from app.repos.firestore_repo import FirestoreRepo


def _ingest_logic(jobId: str, userId: str, pdfId: str, source: dict):
    """
    Core ingestion logic.
    Works for:
    - Local sync execution
    - Celery async execution
    """
    jobs = get_job_repo()
    store = FirestoreRepo()

    try:
        # mark job as processing
        jobs.update(
            jobId,
            status="processing",
            stage="download",
            progress=5
        )

        # ------------------
        # DOWNLOAD
        # ------------------
        pdf_bytes = download_pdf(source)
        jobs.update(jobId, progress=15)

        # ------------------
        # EXTRACT / OCR
        # ------------------
        jobs.update(jobId, stage="extract", progress=30)
        texts, pages, words, ocr_pages = extract_pages(pdf_bytes)

        # ------------------
        # EMBEDDINGS (Pinecone)
        # ------------------
        jobs.update(jobId, stage="embed", progress=60)
        build_embeddings(
            userId=userId,
            pdfId=pdfId,
            page_texts=texts
        )

        # ------------------
        # SUMMARY
        # ------------------
        jobs.update(jobId, stage="summary", progress=80)
        summary = summarize("\n".join(texts), pages, words)

        # ------------------
        # SAVE RESULT
        # ------------------
        store.save(pdfId, {
            "userId": userId,
            "summary": summary,
            "meta": {
                "pages": pages,
                "totalWords": words,
                "ocrPages": ocr_pages
            },
            "status": "ready"
        })

        # mark job done
        jobs.complete(jobId)

    except Exception as e:
        jobs.fail(jobId, str(e))
        store.fail(pdfId, str(e))
        raise


@celery.task(bind=True, name="ingest_pdf")
def ingest_pdf(self, jobId: str, userId: str, pdfId: str, source: dict):
    return _ingest_logic(jobId, userId, pdfId, source)
