import re

from app.schemas.guardrail_schema import RAGGuardrailResult
from app.schemas.rag_schema import RAGAnswer


UNSAFE_PATTERNS = [
    r"\btake\s+\d+\s*(mg|g|mcg|iu)\b",
    r"\byou should take\b",
    r"\bi recommend taking\b",
    r"\bstart taking\b",
    r"\bstop taking\b",
    r"\bincrease your dose\b",
    r"\bdecrease your dose\b",
    r"\bprescribed dose\b",
    r"\bdiagnose\b",
    r"\bdiagnosis is\b",
    r"\btreatment plan\b",
]

OVERCERTAINTY_PATTERNS = [
    r"\bproves\b",
    r"\bguaranteed\b",
    r"\bdefinitely\b",
    r"\bwithout risk\b",
    r"\bno risk\b",
    r"\bcures\b",
    r"\bcure aging\b",
    r"\bstops aging\b",
    r"\breverses aging\b",
]

LIMITATION_SIGNALS = [
    "limited",
    "preliminary",
    "insufficient",
    "not enough",
    "unclear",
    "animal",
    "preclinical",
    "small",
    "needs replication",
    "not medical",
    "does not provide",
]


def _contains_pattern(text: str, patterns: list[str]) -> list[str]:
    found = []

    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(pattern)

    return found


def evaluate_rag_answer(answer: RAGAnswer) -> RAGGuardrailResult:
    """
    Deterministic RAG answer guardrail.

    This does not prove the answer is perfect.
    It catches obvious failure modes:
    - no context
    - no safety note
    - unsafe medical wording
    - overconfident claims
    - missing limitations
    """
    issues = []
    warnings = []

    combined_text = " ".join(
        [
            answer.question,
            answer.answer,
            answer.evidence_summary,
            " ".join(answer.limitations),
            answer.safety_note,
            " ".join(ctx.text_preview for ctx in answer.retrieved_context),
        ]
    ).lower()

    if not answer.answer.strip():
        issues.append("Answer is empty.")

    if not answer.evidence_summary.strip():
        issues.append("Evidence summary is empty.")

    if not answer.safety_note.strip():
        issues.append("Safety note is missing.")

    if not answer.retrieved_context:
        issues.append("No retrieved context attached to answer.")

    if not answer.limitations:
        warnings.append("No explicit limitations were listed.")

    unsafe_hits = _contains_pattern(combined_text, UNSAFE_PATTERNS)
    if unsafe_hits:
        issues.append(
            "Potential unsafe medical advice wording detected: "
            + ", ".join(unsafe_hits)
        )

    overcertainty_hits = _contains_pattern(combined_text, OVERCERTAINTY_PATTERNS)
    if overcertainty_hits:
        warnings.append(
            "Potential overconfident wording detected: "
            + ", ".join(overcertainty_hits)
        )

    if not any(signal in combined_text for signal in LIMITATION_SIGNALS):
        warnings.append(
            "No clear limitation signal detected. RAG answers should usually mention uncertainty or evidence limits."
        )

    if issues:
        severity = "high"
        passed = False
        recommended_action = (
            "Do not trust or present this answer as-is. Regenerate with stricter grounding and safety instructions."
        )
    elif warnings:
        severity = "medium"
        passed = True
        recommended_action = (
            "Answer passed hard guardrails, but review warnings before using externally."
        )
    else:
        severity = "none"
        passed = True
        recommended_action = "Answer passed grounding and safety guardrails."

    return RAGGuardrailResult(
        passed=passed,
        severity=severity,
        issues=issues,
        warnings=warnings,
        recommended_action=recommended_action,
    )
