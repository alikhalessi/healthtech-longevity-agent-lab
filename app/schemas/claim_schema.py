from pydantic import BaseModel, Field
from typing import List


class ExtractedClaim(BaseModel):
    claim_text: str = Field(description="The extracted health-tech or longevity claim")
    claim_type: str = Field(description="supplement, drug, wearable, biomarker, lifestyle, AI health, biotech, unclear, or other")
    why_it_matters: str = Field(description="Why this claim matters for evidence analysis")
    confidence: str = Field(description="high, medium, or low")


class ClaimExtractionResult(BaseModel):
    source_title: str
    extraction_summary: str
    claims: List[ExtractedClaim]
