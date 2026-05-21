import json
import re
from datetime import datetime
from pathlib import Path
from typing import List

from app.schemas.source_schema import SourceRecord
from app.schemas.chunk_schema import SourceChunk
from app.services.source_library import list_sources, load_source_by_path


CHUNKS_DIR = Path("data") / "chunks"
CHUNKS_FILE = CHUNKS_DIR / "source_chunks.jsonl"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_text_into_chunks(
    text: str,
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> List[str]:
    """
    Simple character-based chunking with overlap.

    Later we can replace this with semantic chunking.
    For now, this is stable, transparent, and noob-proof.
    """
    text = normalize_whitespace(text)

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + max_chars, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(0, end - overlap_chars)

    return chunks


def chunk_source(
    source: SourceRecord,
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> List[SourceChunk]:
    raw_chunks = split_text_into_chunks(
        text=source.text,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )

    created_at = datetime.now().isoformat(timespec="seconds")

    chunks = []
    for index, chunk_text in enumerate(raw_chunks, start=1):
        chunk_id = f"{source.source_id}_chunk_{index:04d}"

        chunks.append(
            SourceChunk(
                chunk_id=chunk_id,
                source_id=source.source_id,
                source_title=source.title,
                source_type=source.source_type,
                source_url=source.url,
                tags=source.tags,
                chunk_index=index,
                text=chunk_text,
                character_count=len(chunk_text),
                created_at=created_at,
            )
        )

    return chunks


def rebuild_chunk_library(
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> tuple[int, Path]:
    """
    Rebuild all chunks from all saved local sources.

    This overwrites data/chunks/source_chunks.jsonl.
    """
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    all_source_rows = list_sources()
    all_chunks: List[SourceChunk] = []

    for row in all_source_rows:
        source = load_source_by_path(row["path"])
        chunks = chunk_source(
            source=source,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
        all_chunks.extend(chunks)

    with CHUNKS_FILE.open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")

    return len(all_chunks), CHUNKS_FILE


def load_chunks() -> List[SourceChunk]:
    if not CHUNKS_FILE.exists():
        return []

    chunks = []
    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(SourceChunk(**json.loads(line)))

    return chunks


def search_chunks(query: str, limit: int = 10) -> List[SourceChunk]:
    """
    Very simple keyword search over chunks.

    This is not real vector RAG yet.
    It is the bridge before embeddings.
    """
    query = query.lower().strip()
    chunks = load_chunks()

    if not query:
        return chunks[:limit]

    scored = []

    for chunk in chunks:
        haystack = " ".join(
            [
                chunk.source_title,
                chunk.source_type,
                " ".join(chunk.tags),
                chunk.text,
            ]
        ).lower()

        score = haystack.count(query)

        # Also give weak score for partial word matches.
        for token in query.split():
            if token in haystack:
                score += 1

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [chunk for _, chunk in scored[:limit]]
