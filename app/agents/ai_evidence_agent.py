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
- Flag overclaiming and study limitations.
- Avoid medical diagnosis or treatment advice.

Return only the structured EvidenceReport object.

Important:
Set fine_tune_candidate to true when the claim has any of the following:
- weak evidence
- limited human evidence
- animal/preclinical evidence
- hype or marketing language
- unclear intervention
- small sample size
- modest effect
- needs replication
- overclaiming risk

Be cautious. If the claim is based only on animals, cells, supplements, influencer content, or weak evidence, say so clearly.
"""


def normalize_report(report: EvidenceReport) -> EvidenceReport:
    """
    Deterministic safety/consistency layer after AI output.

    The AI can reason well but may be inconsistent with boolean flags.
    This layer enforces our project rule:
    if there are meaningful limitations or risk flags, keep the example as
    a fine-tuning/eval candidate.
    """
    evidence_level = report.evidence_level.lower()
    human_evidence = report.human_evidence.lower()
    animal_evidence = report.animal_evidence.lower()
    risk_text = " ".join(report.risk_flags).lower()

    candidate_triggers = [
        bool(report.risk_flags),
        "weak" in evidence_level,
        "limited" in evidence_level,
        "unclear" in evidence_level,
        "mixed" in evidence_level,
        human_evidence in ["limited", "unclear", "none"],
        animal_evidence in ["limited", "moderate", "strong"],
        "small sample" in risk_text,
        "modest" in risk_text,
        "replication" in risk_text,
        "hype" in risk_text,
        "overclaim" in risk_text,
        "preclinical" in risk_text,
        "animal" in risk_text,
    ]

    if any(candidate_triggers) and not report.fine_tune_candidate:
        return report.model_copy(update={"fine_tune_candidate": True})

    return report


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

    return normalize_report(response.output_parsed)
