# Architecture

## Purpose

HealthTech Longevity Agent Lab analyzes health-tech and longevity claims using both local rule-based logic and OpenAI-powered structured analysis.

The system supports:

- evidence grading
- hype detection
- claim-risk classification
- local report generation
- fine-tuning candidate collection
- evaluation-driven improvement

## High-Level Flow

User claim/article
?
Streamlit dashboard
?
Analysis mode selector
+-- Local rule-based analyzer
+-- OpenAI AI analyzer
?
EvidenceReport schema
?
Report writer
?
Fine-tune candidate logger
?
Eval runner

## Core Components

### Dashboard

Path:

app/ui/dashboard.py

Responsibilities:

- accepts user text
- lets user choose Local or OpenAI mode
- displays structured evidence report
- saves JSON reports
- saves fine-tune candidates

### Local Analyzer

Path:

app/agents/evidence_agent.py

Responsibilities:

- rule-based evidence classification
- hype word detection
- human/animal evidence detection
- fallback mode without API access

### OpenAI Analyzer

Path:

app/agents/ai_evidence_agent.py

Responsibilities:

- calls OpenAI API
- produces structured EvidenceReport output
- normalizes fine_tune_candidate decisions using deterministic guardrails

### Evidence Schema

Path:

app/schemas/evidence_schema.py

Defines:

- topic
- main_claim
- evidence_level
- human_evidence
- animal_evidence
- hype_score
- risk_flags
- safe_summary
- fine_tune_candidate

### Report Writer

Path:

app/services/report_writer.py

Saves local JSON reports to:

reports/

Reports are ignored by Git.

### Fine-Tune Logger

Path:

app/services/finetune_logger.py

Saves local JSONL examples to:

finetune_candidates/claim_classifier.jsonl

Generated JSONL files are ignored by Git to avoid leaking sensitive user text.

### Eval Runner

Path:

scripts/run_evals.py

Commands:

python scripts/run_evals.py --mode local
python scripts/run_evals.py --mode ai

Local evals are used in GitHub Actions. AI evals are run manually because they require API access.

## Safety Boundary

This project is for research, education, evidence analysis, and portfolio development.

It does not provide:

- medical diagnosis
- treatment recommendations
- medication changes
- personalized clinical decisions

## Current MVP

The MVP supports:

- local analysis
- OpenAI AI analysis
- structured JSON output
- local report saving
- fine-tune candidate logging
- local and AI evals
- GitHub Actions for local evals

## Roadmap

1. Add more eval cases
2. Add source retrieval / RAG
3. Add paper/article ingestion
4. Add PubMed or web-source tracking
5. Add dashboard history view
6. Add visualization of hype/evidence trends
7. Add exportable weekly intelligence reports
8. Add specialist classifiers
9. Add local LLM fallback
10. Prepare a clean fine-tuning dataset
