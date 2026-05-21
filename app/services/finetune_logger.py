import json
from datetime import datetime
from pathlib import Path

from app.schemas.evidence_schema import EvidenceReport


FINETUNE_DIR = Path("finetune_candidates")
FINETUNE_FILE = FINETUNE_DIR / "claim_classifier.jsonl"


def log_finetune_candidate(source_text: str, report: EvidenceReport) -> Path:
    """
    Save one future fine-tuning candidate in JSONL format.

    This does not fine-tune anything yet.
    It only collects clean examples for later eval/fine-tuning work.
    """
    FINETUNE_DIR.mkdir(parents=True, exist_ok=True)

    example = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You classify health-tech and longevity claims. "
                    "Return a structured evidence and hype-risk assessment. "
                    "Do not provide medical diagnosis or treatment advice."
                ),
            },
            {
                "role": "user",
                "content": source_text,
            },
            {
                "role": "assistant",
                "content": json.dumps(report.model_dump(), ensure_ascii=False),
            },
        ],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "failure_or_interest_reason": "weak evidence, hype language, or limited human evidence detected",
    }

    with FINETUNE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(example, ensure_ascii=False) + "\n")

    return FINETUNE_FILE
