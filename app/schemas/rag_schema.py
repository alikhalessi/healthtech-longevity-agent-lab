from pydantic import BaseModel, Field
from typing import List


class RetrievedContext(BaseModel):
    chunk_id: str
    source_title: str
    chunk_index: int
    similarity_score: float
    text_preview: str


class RAGAnswer(BaseModel):
    question: str
    answer: str = Field(description="Answer grounded only in retrieved context")
    evidence_summary: str
    limitations: List[str] = Field(default_factory=list)
    retrieved_context: List[RetrievedContext] = Field(default_factory=list)
    safety_note: str
