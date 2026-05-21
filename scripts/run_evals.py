import argparse
import json
from pathlib import Path

from app.agents.evidence_agent import analyze_text
from app.agents.ai_evidence_agent import analyze_text_with_ai


EVAL_FILE = Path("evals/claim_quality_eval.jsonl")


def load_evals(path: Path):
    examples = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def report_to_search_text(report) -> str:
    parts = [
        report.topic,
        report.main_claim,
        report.evidence_level,
        report.human_evidence,
        report.animal_evidence,
        " ".join(report.risk_flags),
        report.safe_summary,
    ]
    return " ".join(parts).lower()


def evaluate_one(example, report):
    expected = example["expected"]
    failures = []

    expected_ft = expected.get("fine_tune_candidate")
    if expected_ft is not None and report.fine_tune_candidate != expected_ft:
        failures.append(
            f"fine_tune_candidate expected {expected_ft}, got {report.fine_tune_candidate}"
        )

    min_hype = expected.get("min_hype_score", 0)
    if report.hype_score < min_hype:
        failures.append(f"hype_score expected >= {min_hype}, got {report.hype_score}")

    allowed_evidence_terms = expected.get("evidence_level_contains", [])
    if allowed_evidence_terms:
        evidence_lower = report.evidence_level.lower()
        if not any(term.lower() in evidence_lower for term in allowed_evidence_terms):
            failures.append(
                f"evidence_level expected to contain one of {allowed_evidence_terms}, got '{report.evidence_level}'"
            )

    search_text = report_to_search_text(report)
    for keyword in expected.get("risk_keywords", []):
        if keyword.lower() not in search_text:
            failures.append(f"missing risk keyword/context: '{keyword}'")

    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["local", "ai"],
        default="local",
        help="Use local rule-based analyzer or OpenAI AI analyzer.",
    )
    args = parser.parse_args()

    examples = load_evals(EVAL_FILE)

    passed = 0
    failed = 0

    print(f"Running {len(examples)} evals in mode: {args.mode}")
    print("-" * 60)

    for example in examples:
        if args.mode == "ai":
            report = analyze_text_with_ai(example["input"])
        else:
            report = analyze_text(example["input"])

        failures = evaluate_one(example, report)

        if failures:
            failed += 1
            print(f"FAIL: {example['id']}")
            for failure in failures:
                print(f"  - {failure}")
            print("  Report:", report.model_dump())
        else:
            passed += 1
            print(f"PASS: {example['id']}")

    print("-" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
