import json
import math
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.chunk_schema import SourceChunk
from app.services.source_chunker import load_chunks


load_dotenv(override=True)


EMBEDDINGS_DIR = Path("data") / "embeddings"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "chunk_embeddings.jsonl"


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found. Check your local .env file.")

    return OpenAI(api_key=api_key)


def get_embedding_model() -> str:
    return os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def embed_texts(texts: List[str]) -> List[List[float]]:
    client = get_openai_client()
    model = get_embedding_model()

    response = client.embeddings.create(
        model=model,
        input=texts,
    )

    return [item.embedding for item in response.data]


def build_embedding_store(batch_size: int = 50) -> tuple[int, Path]:
    """
    Build local embeddings for all chunks.

    Requires:
    - data/chunks/source_chunks.jsonl already built
    - OPENAI_API_KEY in .env

    Writes:
    - data/embeddings/chunk_embeddings.jsonl
    """
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks()
    records = []

    for start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[start : start + batch_size]
        batch_texts = [chunk.text for chunk in batch_chunks]
        batch_embeddings = embed_texts(batch_texts)

        for chunk, embedding in zip(batch_chunks, batch_embeddings):
            records.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "source_id": chunk.source_id,
                    "source_title": chunk.source_title,
                    "source_type": chunk.source_type,
                    "source_url": chunk.source_url,
                    "tags": chunk.tags,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "character_count": chunk.character_count,
                    "embedding_model": get_embedding_model(),
                    "embedding": embedding,
                }
            )

    with EMBEDDINGS_FILE.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(records), EMBEDDINGS_FILE


def load_embedding_records() -> list[dict]:
    if not EMBEDDINGS_FILE.exists():
        return []

    records = []

    with EMBEDDINGS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records


def semantic_search(query: str, limit: int = 10) -> list[dict]:
    records = load_embedding_records()

    if not records:
        return []

    query_embedding = embed_texts([query])[0]

    scored = []

    for record in records:
        score = cosine_similarity(query_embedding, record["embedding"])
        scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    for score, record in scored[:limit]:
        result = dict(record)
        result["similarity_score"] = round(float(score), 4)
        result.pop("embedding", None)
        results.append(result)

    return results
