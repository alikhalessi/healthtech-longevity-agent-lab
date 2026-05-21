import streamlit as st
from app.agents.evidence_agent import analyze_text
from app.services.report_writer import save_report


st.set_page_config(
    page_title="HealthTech Longevity Agent Lab",
    page_icon="??",
    layout="wide"
)

st.title("HealthTech Longevity Agent Lab")
st.caption("Agentic AI blueprint for longevity evidence analysis, hype detection, evals, and fine-tuning candidates.")

st.warning("Research and education only. Not medical diagnosis or treatment advice.")

sample_text = """A new mouse study suggests that a compound may improve lifespan markers.
However, there is no strong human clinical trial evidence yet. Some articles call it a breakthrough."""

text = st.text_area(
    "Paste a health-tech or longevity claim/article here:",
    value=sample_text,
    height=220
)

if st.button("Analyze"):
    report = analyze_text(text)
    saved_path = save_report(report)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Evidence Level", report.evidence_level)

    with col2:
        st.metric("Human Evidence", report.human_evidence)

    with col3:
        st.metric("Hype Score", report.hype_score)

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

    st.success(f"Report saved locally: {saved_path}")
