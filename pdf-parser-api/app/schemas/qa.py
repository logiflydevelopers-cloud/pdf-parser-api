from pydantic import BaseModel
from typing import List, Optional

class QAHistoryItem(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    question: str
    history: Optional[List[QAHistoryItem]] = None

class AskResponse(BaseModel):
    pdfId: str
    question: str
    answer: str
    answerMode: str
    sources: list
