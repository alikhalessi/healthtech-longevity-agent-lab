import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from app.services.source_chunker import rebuild_chunk_library, load_chunks, search_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap-chars", type=int, default=150)
    parser.add_argument("--search", type=str, default="")
    args = parser.parse_args()

    chunk_count, chunk_path = rebuild_chunk_library(
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
    )

    print(f"Built {chunk_count} chunks")
    print(f"Chunk file: {chunk_path}")

    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    if args.search:
        results = search_chunks(args.search)
        print("-" * 60)
        print(f"Search results for: {args.search}")
        for chunk in results:
            print("-" * 60)
            print(f"Chunk ID: {chunk.chunk_id}")
            print(f"Source: {chunk.source_title}")
            print(f"Text preview: {chunk.text[:300]}...")


if __name__ == "__main__":
    main()
