from app.workers.celery import celery
from app.services.pdf_downloader import download_pdf
from app.services.pdf_extractor import extract_pages
from app.services.summarizer import summarize
from app.services.embeddings import build_embeddings
from app.repos.redis_jobs import get_job_repo
from app.repos.firestore_repo import FirestoreRepo


def _ingest_logic(jobId: str, pdfId: str, source: dict):
    """
    Core ingestion logic.
    Can be called:
    - synchronously (local dev)
    - asynchronously via Celery (production)
    """
    jobs = get_job_repo()
    store = FirestoreRepo()

    try:
        # ------------------
        # DOWNLOAD
        # ------------------
        jobs.update(jobId, stage="download", progress=10)
        pdf_bytes = download_pdf(source)

        # ------------------
        # EXTRACT / OCR
        # ------------------
        jobs.update(jobId, stage="extract", progress=30)
        texts, pages, words, ocr_pages = extract_pages(pdf_bytes)

        # ------------------
        # EMBEDDINGS (Pinecone)
        # ------------------
        jobs.update(jobId, stage="embed", progress=60)
        build_embeddings(pdfId, texts)

        # ------------------
        # SUMMARY
        # ------------------
        jobs.update(jobId, stage="summary", progress=80)
        summary = summarize("\n".join(texts), pages, words)

        # ------------------
        # SAVE RESULT
        # ------------------
        store.save(pdfId, {
            "summary": summary,
            "meta": {
                "pages": pages,
                "totalWords": words,
                "ocrPages": ocr_pages
            },
            "status": "ready"
        })

        jobs.complete(jobId)

    except Exception as e:
        jobs.fail(jobId, str(e))
        store.fail(pdfId, str(e))
        raise


@celery.task(bind=True, name="ingest_pdf")
def ingest_pdf(self, jobId: str, pdfId: str, source: dict):
    """
    Celery task wrapper.
    Production only.
    """
    return _ingest_logic(jobId, pdfId, source)
