# HealthTech Longevity Agent Lab

An agentic AI research and portfolio project for analyzing health-tech and longevity claims.

This project combines:

- local rule-based analysis
- OpenAI-powered structured analysis
- evidence grading
- hype and overclaim detection
- local JSON report saving
- fine-tuning candidate logging
- evaluation-driven improvement

## Why This Project Exists

Health-tech and longevity claims are often surrounded by hype, weak evidence, animal-only studies, supplement marketing, and premature claims about human benefits.

This project creates a small but serious AI-assisted system for asking:

Is this claim supported by strong human evidence, or is it mostly early-stage hype?

## Core Features

- Paste a health-tech or longevity claim/article
- Choose analysis mode:
  - Local rule-based
  - OpenAI AI
- Extract the main claim
- Estimate evidence strength
- Identify human vs animal/preclinical evidence
- Detect hype and marketing language
- Flag overclaiming risk
- Save structured JSON reports locally
- Save fine-tuning candidates locally as JSONL
- Run local and AI evals

## Project Status

MVP v1 is working.

Current capabilities:

- Streamlit dashboard
- Local analyzer
- OpenAI structured analyzer
- Pydantic EvidenceReport schema
- JSON report writer
- Fine-tune candidate logger
- Eval runner
- GitHub Actions local eval workflow

## Project Structure

app/
  agents/
    evidence_agent.py
    ai_evidence_agent.py
  schemas/
    evidence_schema.py
  services/
    report_writer.py
    finetune_logger.py
  ui/
    dashboard.py

evals/
  claim_quality_eval.jsonl

scripts/
  run_evals.py

docs/
  ARCHITECTURE.md

## Setup

Clone the repo:

git clone https://github.com/alikhalessi/healthtech-longevity-agent-lab.git
cd healthtech-longevity-agent-lab

Create a virtual environment:

python -m venv .venv
.\.venv\Scripts\activate

Install dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt

## Environment Variables

Create a local .env file:

OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.5

Do not commit .env.

## Run the Dashboard

python -m streamlit run app\ui\dashboard.py

Open:

http://localhost:8501

## Run Evals

Local mode:

python scripts\run_evals.py --mode local

OpenAI mode:

python scripts\run_evals.py --mode ai

AI mode requires a valid OpenAI API key.

## Safety Boundary

This project is for research, education, and evidence analysis only.

It does not provide:

- medical diagnosis
- treatment advice
- medication adjustment
- clinical decision-making

## Example Use Case

Input:

A new mouse study suggests that a compound may improve lifespan markers.
However, there is no strong human clinical trial evidence yet.
Some articles call it a breakthrough.

Output includes:

- evidence level
- human evidence status
- animal evidence status
- hype score
- risk flags
- safe summary
- fine-tuning candidate flag

## Roadmap

- Add more eval examples
- Add paper/article ingestion
- Add source retrieval / RAG
- Add PubMed or web tracking
- Add dashboard history
- Add weekly report generation
- Add claim-type classifier
- Add local LLM fallback
- Prepare fine-tuning dataset
- Build portfolio demo screenshots

## License

Research and educational use.
