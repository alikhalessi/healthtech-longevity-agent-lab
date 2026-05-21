import hashlib
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


def normalize_for_hash(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def compute_content_hash(text: str) -> str:
    normalized = normalize_for_hash(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_existing_source_by_hash(content_hash: str) -> tuple[SourceRecord, Path] | None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    for path in SOURCES_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            existing_hash = data.get("content_hash")

            if not existing_hash and data.get("text"):
                existing_hash = compute_content_hash(data["text"])

            if existing_hash == content_hash:
                return SourceRecord(**data), path

        except Exception:
            continue

    return None


def save_source(
    title: str,
    source_text: str,
    source_type: str = "article",
    url: str | None = None,
    tags: List[str] | None = None,
) -> tuple[SourceRecord, Path, bool]:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    content_hash = compute_content_hash(source_text)
    existing = find_existing_source_by_hash(content_hash)

    if existing:
        existing_record, existing_path = existing
        return existing_record, existing_path, False

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
        content_hash=content_hash,
    )

    file_path = SOURCES_DIR / f"{source_id}.json"

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)

    return record, file_path, True


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
                    "content_hash": data.get("content_hash", ""),
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
                    "content_hash": "",
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


def update_source_by_path(
    path_text: str,
    title: str,
    source_text: str,
    source_type: str,
    url: str | None = None,
    tags: List[str] | None = None,
) -> tuple[SourceRecord, Path]:
    path = Path(path_text)

    with path.open("r", encoding="utf-8") as f:
        old_data = json.load(f)

    new_hash = compute_content_hash(source_text)

    for other_path in SOURCES_DIR.glob("*.json"):
        if other_path.resolve() == path.resolve():
            continue

        try:
            with other_path.open("r", encoding="utf-8") as f:
                other_data = json.load(f)

            other_hash = other_data.get("content_hash")
            if not other_hash and other_data.get("text"):
                other_hash = compute_content_hash(other_data["text"])

            if other_hash == new_hash:
                raise ValueError(
                    f"Duplicate detected. This text already exists in: {other_path}"
                )
        except ValueError:
            raise
        except Exception:
            continue

    updated = SourceRecord(
        source_id=old_data.get("source_id", path.stem),
        title=title.strip() or "Untitled source",
        source_type=source_type,
        url=url.strip() if url else None,
        tags=tags or [],
        text=source_text,
        text_preview=source_text[:500],
        character_count=len(source_text),
        created_at=old_data.get("created_at", datetime.now().isoformat(timespec="seconds")),
        content_hash=new_hash,
    )

    with path.open("w", encoding="utf-8") as f:
        json.dump(updated.model_dump(), f, indent=2, ensure_ascii=False)

    return updated, path


def delete_source_by_path(path_text: str) -> Path:
    path = Path(path_text)

    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    path.unlink()
    return path
