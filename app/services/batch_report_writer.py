import json
from datetime import datetime
from pathlib import Path
from typing import List

from app.schemas.claim_schema import ClaimExtractionResult
from app.schemas.evidence_schema import EvidenceReport


BATCH_REPORTS_DIR = Path("reports") / "batch"


def save_batch_report(
    source_title: str,
    source_text: str,
    extraction: ClaimExtractionResult,
    evidence_reports: List[EvidenceReport],
) -> Path:
    BATCH_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_title = "".join(
        char if char.isalnum() or char in ["-", "_"] else "_"
        for char in source_title.strip()[:50]
    ).strip("_")

    if not safe_title:
        safe_title = "untitled_source"

    file_path = BATCH_REPORTS_DIR / f"batch_{timestamp}_{safe_title}.json"

    payload = {
        "source_title": source_title,
        "source_text_preview": source_text[:1000],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "extraction": extraction.model_dump(),
        "evidence_reports": [report.model_dump() for report in evidence_reports],
    }

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return file_path
