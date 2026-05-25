import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from app.services.rag_answerer import answer_question_with_rag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="Question to answer using local retrieved chunks.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of semantic chunks to retrieve.",
    )
    args = parser.parse_args()

    answer = answer_question_with_rag(
        question=args.question,
        limit=args.limit,
    )

    print("=" * 80)
    print("QUESTION")
    print("=" * 80)
    print(answer.question)

    print("=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(answer.answer)

    print("=" * 80)
    print("EVIDENCE SUMMARY")
    print("=" * 80)
    print(answer.evidence_summary)

    print("=" * 80)
    print("LIMITATIONS")
    print("=" * 80)
    for limitation in answer.limitations:
        print(f"- {limitation}")

    print("=" * 80)
    print("RETRIEVED CONTEXT")
    print("=" * 80)
    for ctx in answer.retrieved_context:
        print(f"- {ctx.source_title} | {ctx.chunk_id} | score={ctx.similarity_score}")

    print("=" * 80)
    print("SAFETY NOTE")
    print("=" * 80)
    print(answer.safety_note)


if __name__ == "__main__":
    main()
