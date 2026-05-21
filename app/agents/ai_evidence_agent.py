import os
from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.evidence_schema import EvidenceReport


load_dotenv(override=True)


SYSTEM_PROMPT = """
You are a health-tech and longevity evidence analysis assistant.

Your task:
- Extract the main claim.
- Estimate evidence strength.
- Identify whether evidence is human, animal/preclinical, unclear, or mixed.
- Detect hype/marketing language.
- Flag overclaiming.
- Avoid medical diagnosis or treatment advice.

Return only the structured EvidenceReport object.
Be cautious. If the claim is based only on animals, cells, supplements, influencer content, or weak evidence, say so clearly.
"""


def analyze_text_with_ai(text: str) -> EvidenceReport:
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
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        text_format=EvidenceReport,
    )

    return response.output_parsed
