# HealthTech Longevity Agent Lab

An agentic AI research lab for health-tech and longevity evidence analysis.

## Goal

This project builds a Level 3 agentic workflow and prepares Level 4 fine-tuning datasets for narrow health-tech/longevity tasks.

## Core Features

- Extract health and longevity claims from text
- Grade evidence strength
- Detect hype and unsafe overclaims
- Generate structured reports
- Save failure examples for future fine-tuning
- Build evaluation datasets

## First MVP

Paste a health-tech or longevity article into the app and receive:

- extracted claim
- evidence level
- human evidence status
- animal evidence status
- hype score
- risk flags
- plain-English summary
- fine-tuning candidate flag

## Project Structure

app/
  agents/
  api/
  core/
  schemas/
  services/
  ui/

data/
  raw/
  processed/
  demo/
  vector_store/

evals/
finetune_candidates/
reports/
notebooks/
tests/
docs/

## Roadmap

1. Create basic Streamlit dashboard
2. Add evidence extraction agent
3. Add evidence grading schema
4. Save structured reports
5. Add evaluation examples
6. Add fine-tuning candidate logger
7. Build portfolio-quality documentation

## Safety Boundary

This project is for research, education, and evidence analysis. It does not provide medical diagnosis or treatment advice.
