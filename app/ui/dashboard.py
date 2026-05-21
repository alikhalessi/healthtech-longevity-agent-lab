import pandas as pd
import streamlit as st

from app.agents.evidence_agent import analyze_text
from app.agents.ai_evidence_agent import analyze_text_with_ai
from app.agents.claim_extractor_agent import extract_claims_with_ai, extract_claims_locally
from app.services.report_writer import save_report
from app.services.batch_report_writer import save_batch_report
from app.services.finetune_logger import log_finetune_candidate


st.set_page_config(
    page_title="HealthTech Longevity Agent Lab",
    page_icon="HL",
    layout="wide",
)

st.title("HealthTech Longevity Agent Lab")
st.caption(
    "Agentic AI blueprint for longevity evidence analysis, hype detection, "
    "evals, source ingestion, and fine-tuning candidates."
)

st.warning("Research and education only. Not medical diagnosis or treatment advice.")


def analyze_claim_text(text: str, mode: str):
    if mode == "OpenAI AI":
        return analyze_text_with_ai(text)
    return analyze_text(text)


tab_single, tab_article = st.tabs(["Single Claim Analysis", "Article / Abstract Ingestion"])


with tab_single:
    st.header("Single Claim Analysis")

    analysis_mode = st.radio(
        "Choose analysis mode:",
        ["Local rule-based", "OpenAI AI"],
        horizontal=True,
        key="single_analysis_mode",
    )

    sample_text = """A new mouse study suggests that a compound may improve lifespan markers.
However, there is no strong human clinical trial evidence yet. Some articles call it a breakthrough."""

    text = st.text_area(
        "Paste a health-tech or longevity claim here:",
        value=sample_text,
        height=220,
        key="single_claim_text",
    )

    if st.button("Analyze Single Claim"):
        try:
            report = analyze_claim_text(text, analysis_mode)
            saved_report_path = save_report(report)

            fine_tune_path = None
            if report.fine_tune_candidate:
                fine_tune_path = log_finetune_candidate(text, report)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Evidence Level", report.evidence_level)

            with col2:
                st.metric("Human Evidence", report.human_evidence)

            with col3:
                st.metric("Hype Score", report.hype_score)

            with col4:
                st.metric("Fine-tune Candidate", "Yes" if report.fine_tune_candidate else "No")

            st.subheader("Main Claim")
            st.write(report.main_claim)

            st.subheader("Risk Flags")
            if report.risk_flags:
                for flag in report.risk_flags:
                    st.error(flag)
            else:
                st.success("No major risk flags detected.")

            st.subheader("Safe Summary")
            st.write(report.safe_summary)

            st.subheader("Structured JSON Output")
            st.json(report.model_dump())

            st.success(f"Report saved locally: {saved_report_path}")

            if fine_tune_path:
                st.info(f"Fine-tuning candidate saved locally: {fine_tune_path}")
            else:
                st.info("No fine-tuning candidate saved for this input.")

        except Exception as error:
            st.error("Analysis failed.")
            st.exception(error)


with tab_article:
    st.header("Article / Abstract Ingestion")

    source_title = st.text_input(
        "Source title:",
        value="Untitled longevity source",
    )

    extraction_mode = st.radio(
        "Claim extraction mode:",
        ["OpenAI AI", "Local simple"],
        horizontal=True,
        key="article_extraction_mode",
    )

    claim_analysis_mode = st.radio(
        "Claim analysis mode:",
        ["OpenAI AI", "Local rule-based"],
        horizontal=True,
        key="article_analysis_mode",
    )

    article_sample = """A new mouse study suggests that a compound may improve lifespan markers.
The authors report changes in mitochondrial function and inflammatory biomarkers.
However, no strong human clinical trial evidence is available yet.
Some media articles describe the finding as a breakthrough for reverse aging."""

    article_text = st.text_area(
        "Paste article, abstract, or long source text here:",
        value=article_sample,
        height=320,
        key="article_text",
    )

    if st.button("Extract Claims and Analyze"):
        try:
            if extraction_mode == "OpenAI AI":
                extraction = extract_claims_with_ai(article_text, source_title)
            else:
                extraction = extract_claims_locally(article_text, source_title)

            st.subheader("Extraction Summary")
            st.write(extraction.extraction_summary)

            if not extraction.claims:
                st.warning("No claims were extracted.")
            else:
                evidence_reports = []
                rows = []

                for index, claim in enumerate(extraction.claims, start=1):
                    report = analyze_claim_text(claim.claim_text, claim_analysis_mode)
                    evidence_reports.append(report)

                    save_report(report)

                    if report.fine_tune_candidate:
                        log_finetune_candidate(claim.claim_text, report)

                    rows.append(
                        {
                            "claim_number": index,
                            "claim_text": claim.claim_text,
                            "claim_type": claim.claim_type,
                            "claim_confidence": claim.confidence,
                            "evidence_level": report.evidence_level,
                            "human_evidence": report.human_evidence,
                            "animal_evidence": report.animal_evidence,
                            "hype_score": report.hype_score,
                            "fine_tune_candidate": report.fine_tune_candidate,
                            "risk_flags": "; ".join(report.risk_flags),
                        }
                    )

                batch_path = save_batch_report(
                    source_title=source_title,
                    source_text=article_text,
                    extraction=extraction,
                    evidence_reports=evidence_reports,
                )

                st.subheader("Extracted Claims and Evidence Analysis")
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

                st.subheader("Detailed Claim Reports")
                for index, row in enumerate(rows, start=1):
                    with st.expander(f"Claim {index}: {row['claim_text'][:80]}"):
                        st.write("Claim type:", row["claim_type"])
                        st.write("Extraction confidence:", row["claim_confidence"])
                        st.write("Evidence level:", row["evidence_level"])
                        st.write("Human evidence:", row["human_evidence"])
                        st.write("Animal evidence:", row["animal_evidence"])
                        st.write("Hype score:", row["hype_score"])
                        st.write("Fine-tune candidate:", row["fine_tune_candidate"])
                        st.write("Risk flags:", row["risk_flags"])

                st.success(f"Batch report saved locally: {batch_path}")

        except Exception as error:
            st.error("Article ingestion failed.")
            st.exception(error)
