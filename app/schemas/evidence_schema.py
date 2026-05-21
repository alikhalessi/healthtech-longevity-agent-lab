from pydantic import BaseModel, Field
from typing import List


class EvidenceReport(BaseModel):
    topic: str = Field(description="Main health-tech or longevity topic")
    main_claim: str = Field(description="Main claim extracted from the text")
    evidence_level: str = Field(description="strong, moderate, weak, mixed, or unclear")
    human_evidence: str = Field(description="none, limited, moderate, strong, or unclear")
    animal_evidence: str = Field(description="none, limited, moderate, strong, or unclear")
    hype_score: int = Field(description="0 to 10 score where 10 means extreme hype")
    risk_flags: List[str] = Field(default_factory=list)
    safe_summary: str
    fine_tune_candidate: bool = False
