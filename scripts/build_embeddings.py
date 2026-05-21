import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from app.services.vector_store import (
    build_embedding_store,
    load_embedding_records,
    semantic_search,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--search", type=str, default="")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    count, path = build_embedding_store(batch_size=args.batch_size)

    print(f"Built {count} embedding records")
    print(f"Embedding file: {path}")

    records = load_embedding_records()
    print(f"Loaded {len(records)} embedding records")

    if args.search:
        print("-" * 60)
        print(f"Semantic search for: {args.search}")
        results = semantic_search(args.search, limit=args.limit)

        for result in results:
            print("-" * 60)
            print(f"Score: {result['similarity_score']}")
            print(f"Source: {result['source_title']}")
            print(f"Chunk ID: {result['chunk_id']}")
            print(f"Preview: {result['text'][:300]}...")


if __name__ == "__main__":
    main()
