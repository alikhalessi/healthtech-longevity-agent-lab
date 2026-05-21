from app.schemas.evidence_schema import EvidenceReport


def analyze_text(text: str) -> EvidenceReport:
    lowered = text.lower()
    risk_flags = []

    hype_terms = {
        "miracle": 3,
        "cure": 3,
        "reverse aging": 3,
        "proven": 2,
        "guaranteed": 3,
        "breakthrough": 2,
        "secret": 2,
        "doctors hate": 3,
        "anti-aging cure": 4,
    }

    matched_hype_terms = []
    hype_score = 0

    for term, weight in hype_terms.items():
        if term in lowered:
            matched_hype_terms.append(term)
            hype_score += weight

    animal_terms = [
        "mouse",
        "mice",
        "rat",
        "rats",
        "animal study",
        "animal model",
        "preclinical",
    ]

    human_terms = [
        "human trial",
        "clinical trial",
        "randomized trial",
        "rct",
        "meta-analysis",
        "systematic review",
    ]

    negative_human_phrases = [
        "no strong human",
        "no human evidence",
        "without human evidence",
        "not tested in humans",
        "no clinical evidence",
        "no strong clinical",
        "no strong human clinical trial evidence",
    ]

    has_animal_evidence = any(term in lowered for term in animal_terms)
    has_human_evidence = any(term in lowered for term in human_terms)
    has_negative_human_phrase = any(phrase in lowered for phrase in negative_human_phrases)

    if has_animal_evidence:
        animal_evidence = "moderate"
        risk_flags.append("Animal or preclinical evidence detected")
    else:
        animal_evidence = "unclear"

    if has_negative_human_phrase:
        human_evidence = "limited"
        risk_flags.append("Human evidence appears limited or not strong")
    elif has_human_evidence:
        human_evidence = "limited"
    else:
        human_evidence = "unclear"
        risk_flags.append("Human evidence unclear")

    if has_animal_evidence and human_evidence in ["limited", "unclear"]:
        risk_flags.append("Mostly early-stage or animal-based evidence")

    if matched_hype_terms:
        risk_flags.append(
            "Marketing-style or hype language detected: "
            + ", ".join(matched_hype_terms)
        )

    if has_animal_evidence and has_negative_human_phrase:
        hype_score += 1

    if human_evidence == "limited" and animal_evidence == "moderate":
        evidence_level = "weak/mixed"
    elif human_evidence == "unclear":
        evidence_level = "unclear"
    else:
        evidence_level = "mixed"

    fine_tune_candidate = bool(risk_flags)

    return EvidenceReport(
        topic="Longevity / health-tech claim",
        main_claim=text[:180] + "..." if len(text) > 180 else text,
        evidence_level=evidence_level,
        human_evidence=human_evidence,
        animal_evidence=animal_evidence,
        hype_score=min(hype_score, 10),
        risk_flags=risk_flags,
        safe_summary=(
            "This claim needs cautious interpretation. Early animal or limited human evidence "
            "should not be treated as proof of a real longevity benefit in humans."
        ),
        fine_tune_candidate=fine_tune_candidate,
    )
