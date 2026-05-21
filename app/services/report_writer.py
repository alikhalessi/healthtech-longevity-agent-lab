import json
from datetime import datetime
from pathlib import Path
from app.schemas.evidence_schema import EvidenceReport


REPORTS_DIR = Path("reports")


def save_report(report: EvidenceReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = REPORTS_DIR / f"report_{timestamp}.json"

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

    return file_path
