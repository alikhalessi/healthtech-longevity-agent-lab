import json
import re
from datetime import datetime
from pathlib import Path
from typing import List

from app.schemas.source_schema import SourceRecord


SOURCES_DIR = Path("data") / "sources"


def slugify(text: str, max_length: int = 50) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:max_length] or "untitled_source"


def save_source(
    title: str,
    source_text: str,
    source_type: str = "article",
    url: str | None = None,
    tags: List[str] | None = None,
) -> tuple[SourceRecord, Path]:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = slugify(title)
    source_id = f"{timestamp}_{slug}"

    record = SourceRecord(
        source_id=source_id,
        title=title.strip() or "Untitled source",
        source_type=source_type,
        url=url.strip() if url else None,
        tags=tags or [],
        text=source_text,
        text_preview=source_text[:500],
        character_count=len(source_text),
        created_at=datetime.now().isoformat(timespec="seconds"),
    )

    file_path = SOURCES_DIR / f"{source_id}.json"

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)

    return record, file_path


def list_sources() -> list[dict]:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(SOURCES_DIR.glob("*.json"), reverse=True):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            rows.append(
                {
                    "source_id": data.get("source_id", path.stem),
                    "title": data.get("title", "Untitled"),
                    "source_type": data.get("source_type", "unknown"),
                    "created_at": data.get("created_at", ""),
                    "character_count": data.get("character_count", 0),
                    "tags": ", ".join(data.get("tags", [])),
                    "path": str(path),
                }
            )
        except Exception:
            rows.append(
                {
                    "source_id": path.stem,
                    "title": "Could not read source",
                    "source_type": "error",
                    "created_at": "",
                    "character_count": 0,
                    "tags": "",
                    "path": str(path),
                }
            )

    return rows


def load_source_by_path(path_text: str) -> SourceRecord:
    path = Path(path_text)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return SourceRecord(**data)
