from app.schemas.evidence_schema import EvidenceReport


def analyze_text(text: str) -> EvidenceReport:
    lowered = text.lower()

    hype_score = 3
    risk_flags = []

    hype_words = [
        "miracle",
        "cure",
        "reverse aging",
        "proven",
        "guaranteed",
        "breakthrough",
    ]

    for word in hype_words:
        if word in lowered:
            hype_score += 1

    if "mouse" in lowered or "mice" in lowered or "animal" in lowered:
        animal_evidence = "moderate"
    else:
        animal_evidence = "unclear"

    if "human trial" in lowered or "clinical trial" in lowered:
        human_evidence = "limited"
    else:
        human_evidence = "unclear"
        risk_flags.append("Human evidence unclear")

    if hype_score >= 7:
        risk_flags.append("Possible hype or overclaiming")

    return EvidenceReport(
        topic="Longevity / health-tech claim",
        main_claim=text[:180] + "..." if len(text) > 180 else text,
        evidence_level="unclear",
        human_evidence=human_evidence,
        animal_evidence=animal_evidence,
        hype_score=min(hype_score, 10),
        risk_flags=risk_flags,
        safe_summary=(
            "This is an early structured analysis. It should be treated as "
            "research support, not medical advice."
        ),
        fine_tune_candidate=hype_score >= 7 or human_evidence == "unclear",
    )
