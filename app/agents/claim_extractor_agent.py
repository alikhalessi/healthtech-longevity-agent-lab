import os
import re
from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.claim_schema import ClaimExtractionResult, ExtractedClaim


load_dotenv(override=True)


CLAIM_EXTRACTION_PROMPT = """
You are a cautious health-tech and longevity claim extraction assistant.

Your task:
- Read the user's article, abstract, or pasted text.
- Extract the main health-tech/longevity claims.
- Focus on claims that need evidence checking.
- Ignore generic background sentences.
- Do not give medical advice.
- Do not diagnose or recommend treatment.

Return a structured ClaimExtractionResult.

Extract between 1 and 8 claims.
If the text contains hype, supplement claims, animal studies, biomarker claims, wearable claims, or AI-health claims, capture them clearly.
"""


def extract_claims_with_ai(source_text: str, source_title: str = "Untitled source") -> ClaimExtractionResult:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5.5")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found. Check your local .env file.")

    client = OpenAI(api_key=api_key)

    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": CLAIM_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": f"Source title: {source_title}\n\nSource text:\n{source_text}",
            },
        ],
        text_format=ClaimExtractionResult,
    )

    return response.output_parsed


def extract_claims_locally(source_text: str, source_title: str = "Untitled source") -> ClaimExtractionResult:
    """
    Simple local fallback.

    This is intentionally primitive. It extracts sentences containing common
    health/longevity signal words.
    """
    keywords = [
        "longevity",
        "lifespan",
        "healthspan",
        "aging",
        "anti-aging",
        "biomarker",
        "sleep",
        "hrv",
        "blood pressure",
        "glucose",
        "inflammation",
        "supplement",
        "clinical trial",
        "mouse",
        "mice",
        "animal",
        "wearable",
        "ai",
        "algorithm",
        "diagnosis",
        "risk",
        "prediction",
        "breakthrough",
        "cure",
        "reverse aging",
    ]

    sentences = re.split(r"(?<=[.!?])\s+", source_text.strip())
    selected = []

    for sentence in sentences:
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            selected.append(sentence.strip())

    selected = selected[:8]

    if not selected and source_text.strip():
        selected = [source_text.strip()[:300]]

    claims = [
        ExtractedClaim(
            claim_text=sentence,
            claim_type="unclear",
            why_it_matters="This sentence may contain a health-tech or longevity claim that needs evidence review.",
            confidence="low",
        )
        for sentence in selected
    ]

    return ClaimExtractionResult(
        source_title=source_title,
        extraction_summary="Local keyword-based extraction. Use OpenAI mode for stronger claim extraction.",
        claims=claims,
    )
