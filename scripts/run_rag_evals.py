import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from app.services.rag_answerer import answer_question_with_rag


EVAL_FILE = PROJECT_ROOT / "evals" / "rag_answer_eval.jsonl"


def load_evals(path: Path):
    examples = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    return examples


def answer_to_text(answer) -> str:
    parts = [
        answer.question,
        answer.answer,
        answer.evidence_summary,
        " ".join(answer.limitations),
        answer.safety_note,
        " ".join(ctx.text_preview for ctx in answer.retrieved_context),
    ]

    return " ".join(parts).lower()


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms)


def evaluate_one(example: dict, answer) -> list[str]:
    expected = example["expected"]
    failures = []

    if not answer.answer.strip():
        failures.append("answer is empty")

    if not answer.evidence_summary.strip():
        failures.append("evidence_summary is empty")

    if not answer.safety_note.strip():
        failures.append("safety_note is empty")

    min_contexts = expected.get("min_contexts", 1)
    if len(answer.retrieved_context) < min_contexts:
        failures.append(
            f"expected at least {min_contexts} retrieved contexts, got {len(answer.retrieved_context)}"
        )

    blob = answer_to_text(answer)

    required_any = expected.get("required_any", [])
    if required_any and not contains_any(blob, required_any):
        failures.append(f"missing expected topic signal; wanted one of {required_any}")

    forbidden_any = expected.get("forbidden_any", [])
    found_forbidden = [term for term in forbidden_any if term.lower() in blob]
    if found_forbidden:
        failures.append(f"forbidden unsafe phrase(s) found: {found_forbidden}")

    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of retrieved chunks per RAG question.",
    )
    args = parser.parse_args()

    examples = load_evals(EVAL_FILE)

    passed = 0
    failed = 0

    print(f"Running {len(examples)} RAG evals")
    print("-" * 80)

    for example in examples:
        print(f"Evaluating: {example['id']}")

        answer = answer_question_with_rag(
            question=example["question"],
            limit=args.limit,
        )

        failures = evaluate_one(example, answer)

        if failures:
            failed += 1
            print(f"FAIL: {example['id']}")
            for failure in failures:
                print(f"  - {failure}")
            print("  Answer:", answer.answer)
            print("  Evidence summary:", answer.evidence_summary)
            print("  Limitations:", answer.limitations)
            print("  Safety note:", answer.safety_note)
            print(
                "  Retrieved contexts:",
                [
                    {
                        "chunk_id": ctx.chunk_id,
                        "source_title": ctx.source_title,
                        "score": ctx.similarity_score,
                    }
                    for ctx in answer.retrieved_context
                ],
            )
        else:
            passed += 1
            print(f"PASS: {example['id']}")

        print("-" * 80)

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
