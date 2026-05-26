from pydantic import BaseModel, Field
from typing import List


class RAGGuardrailResult(BaseModel):
    passed: bool
    severity: str = Field(description="none, low, medium, or high")
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommended_action: str
