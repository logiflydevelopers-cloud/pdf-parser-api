from pydantic import BaseModel
from typing import Optional, Dict, Any

class JobStatus(BaseModel):
    jobId: str
    status: str
    stage: Optional[str] = None
    progress: Optional[int] = None
    error: Optional[str] = None
    pdfId: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
