from pydantic import BaseModel
from typing import Optional

class PDFSource(BaseModel):
    type: str  # "url" | "firebase_storage"
    url: Optional[str] = None
    bucket: Optional[str] = None
    path: Optional[str] = None

class IngestRequest(BaseModel):
    userId: str
    pdfId: str
    fileName: str
    source: PDFSource

class IngestResponse(BaseModel):
    pdfId: str
    jobId: str
    status: str

