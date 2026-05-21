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
                    "text_preview": data.get("text_preview", ""),
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
                    "text_preview": "",
                    "path": str(path),
                }
            )

    return rows


def get_available_source_types(rows: list[dict]) -> list[str]:
    source_types = sorted(
        {row.get("source_type", "unknown") for row in rows if row.get("source_type")}
    )
    return ["All"] + source_types


def get_available_tags(rows: list[dict]) -> list[str]:
    tag_set = set()

    for row in rows:
        tags_text = row.get("tags", "")
        for tag in tags_text.split(","):
            cleaned = tag.strip()
            if cleaned:
                tag_set.add(cleaned)

    return ["All"] + sorted(tag_set)


def filter_sources(
    rows: list[dict],
    search_query: str = "",
    source_type_filter: str = "All",
    tag_filter: str = "All",
) -> list[dict]:
    query = search_query.lower().strip()
    filtered = []

    for row in rows:
        row_text = " ".join(
            [
                row.get("source_id", ""),
                row.get("title", ""),
                row.get("source_type", ""),
                row.get("tags", ""),
                row.get("text_preview", ""),
                row.get("created_at", ""),
            ]
        ).lower()

        matches_query = not query or query in row_text
        matches_type = source_type_filter == "All" or row.get("source_type") == source_type_filter
        matches_tag = tag_filter == "All" or tag_filter in row.get("tags", "")

        if matches_query and matches_type and matches_tag:
            filtered.append(row)

    return filtered


def load_source_by_path(path_text: str) -> SourceRecord:
    path = Path(path_text)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return SourceRecord(**data)
