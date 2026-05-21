import pandas as pd
import streamlit as st

from app.agents.evidence_agent import analyze_text
from app.agents.ai_evidence_agent import analyze_text_with_ai
from app.agents.claim_extractor_agent import extract_claims_with_ai, extract_claims_locally
from app.services.report_writer import save_report
from app.services.batch_report_writer import save_batch_report
from app.services.finetune_logger import log_finetune_candidate
from app.services.source_library import save_source, list_sources, load_source_by_path, filter_sources, get_available_source_types, get_available_tags, update_source_by_path, delete_source_by_path, update_source_by_path, delete_source_by_path
from app.services.source_chunker import rebuild_chunk_library, load_chunks, search_chunks
from app.services.vector_store import build_embedding_store, load_embedding_records, semantic_search


st.set_page_config(
    page_title="HealthTech Longevity Agent Lab",
    page_icon="HL",
    layout="wide",
)

st.title("HealthTech Longevity Agent Lab")
st.caption(
    "Agentic AI blueprint for longevity evidence analysis, hype detection, "
    "evals, source ingestion, source library, and fine-tuning candidates."
)

st.warning("Research and education only. Not medical diagnosis or treatment advice.")


def analyze_claim_text(text: str, mode: str):
    if mode == "OpenAI AI":
        return analyze_text_with_ai(text)
    return analyze_text(text)


def run_article_pipeline(
    source_title: str,
    article_text: str,
    extraction_mode: str,
    claim_analysis_mode: str,
):
    if extraction_mode == "OpenAI AI":
        extraction = extract_claims_with_ai(article_text, source_title)
    else:
        extraction = extract_claims_locally(article_text, source_title)

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

    return extraction, rows, batch_path


tab_single, tab_article, tab_library, tab_chunks, tab_vector = st.tabs(
    [
        "Single Claim Analysis",
        "Article / Abstract Ingestion",
        "Source Library",
        "Chunk Search / RAG Prep",
        "Vector Search / Semantic RAG",
    ]
)


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
        key="article_source_title",
    )

    source_url = st.text_input(
        "Source URL or reference, optional:",
        value="",
        key="article_source_url",
    )

    source_type = st.selectbox(
        "Source type:",
        ["article", "abstract", "paper", "web_text", "note", "other"],
        key="article_source_type",
    )

    tags_text = st.text_input(
        "Tags, comma-separated:",
        value="longevity, evidence",
        key="article_tags",
    )

    save_to_library = st.checkbox(
        "Save this source to local source library",
        value=True,
        key="save_to_library",
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

    if st.button("Save Source, Extract Claims, and Analyze"):
        try:
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            if save_to_library:
                source_record, source_path, was_created_new = save_source(
                    title=source_title,
                    source_text=article_text,
                    source_type=source_type,
                    url=source_url,
                    tags=tags,
                )
                if was_created_new:
                    st.success(f"Source saved locally: {source_path}")
                else:
                    st.warning(f"Duplicate source detected. Existing source reused: {source_path}")
                st.caption(f"Source ID: {source_record.source_id}")

            extraction, rows, batch_path = run_article_pipeline(
                source_title=source_title,
                article_text=article_text,
                extraction_mode=extraction_mode,
                claim_analysis_mode=claim_analysis_mode,
            )

            st.subheader("Extraction Summary")
            st.write(extraction.extraction_summary)

            if not extraction.claims:
                st.warning("No claims were extracted.")
            else:
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


with tab_library:
    st.header("Source Library")

    st.write(
        "Saved sources are stored locally in data/sources/ and ignored by Git. "
        "This keeps private pasted source text out of GitHub."
    )

    all_sources = list_sources()

    if not all_sources:
        st.info("No saved sources yet.")
    else:
        st.subheader("Search and Filter")

        col_search, col_type, col_tag = st.columns([2, 1, 1])

        with col_search:
            search_query = st.text_input(
                "Search title, tags, source ID, or preview text:",
                value="",
                key="library_search_query",
            )

        with col_type:
            source_type_filter = st.selectbox(
                "Source type:",
                get_available_source_types(all_sources),
                key="library_source_type_filter",
            )

        with col_tag:
            tag_filter = st.selectbox(
                "Tag:",
                get_available_tags(all_sources),
                key="library_tag_filter",
            )

        filtered_sources = filter_sources(
            rows=all_sources,
            search_query=search_query,
            source_type_filter=source_type_filter,
            tag_filter=tag_filter,
        )

        st.caption(f"Showing {len(filtered_sources)} of {len(all_sources)} saved sources.")

        if not filtered_sources:
            st.warning("No sources match the current filters.")
        else:
            sources_df = pd.DataFrame(filtered_sources)

            st.subheader("Saved Sources")
            visible_columns = [
                "created_at",
                "title",
                "source_type",
                "character_count",
                "tags",
                "source_id",
            ]
            st.dataframe(
                sources_df[visible_columns],
                use_container_width=True,
            )

            options = {
                f"{row['created_at']} | {row['title']} | {row['source_id']}": row["path"]
                for row in filtered_sources
            }

            selected_label = st.selectbox(
                "Select a source to inspect or re-analyze:",
                list(options.keys()),
            )

            selected_path = options[selected_label]
            selected_source = load_source_by_path(selected_path)

            st.subheader("Selected Source")
            st.write("Title:", selected_source.title)
            st.write("Type:", selected_source.source_type)
            st.write("URL:", selected_source.url or "None")
            st.write("Tags:", ", ".join(selected_source.tags) if selected_source.tags else "None")
            st.write("Character count:", selected_source.character_count)
            st.write("Created at:", selected_source.created_at)

            st.text_area(
                "Source text preview:",
                value=selected_source.text[:3000],
                height=280,
                disabled=True,
            )

            with st.expander("Edit or Delete Selected Source"):
                edited_title = st.text_input(
                    "Edit title:",
                    value=selected_source.title,
                    key=f"edit_title_{selected_source.source_id}",
                )

                edited_url = st.text_input(
                    "Edit URL/reference:",
                    value=selected_source.url or "",
                    key=f"edit_url_{selected_source.source_id}",
                )

                source_type_options = ["article", "abstract", "paper", "web_text", "note", "other"]
                selected_type_index = (
                    source_type_options.index(selected_source.source_type)
                    if selected_source.source_type in source_type_options
                    else 0
                )

                edited_source_type = st.selectbox(
                    "Edit source type:",
                    source_type_options,
                    index=selected_type_index,
                    key=f"edit_type_{selected_source.source_id}",
                )

                edited_tags_text = st.text_input(
                    "Edit tags, comma-separated:",
                    value=", ".join(selected_source.tags),
                    key=f"edit_tags_{selected_source.source_id}",
                )

                edited_text = st.text_area(
                    "Edit full source text:",
                    value=selected_source.text,
                    height=360,
                    key=f"edit_text_{selected_source.source_id}",
                )

                col_save, col_delete = st.columns(2)

                with col_save:
                    if st.button("Save Source Edits"):
                        try:
                            edited_tags = [
                                tag.strip()
                                for tag in edited_tags_text.split(",")
                                if tag.strip()
                            ]

                            updated_source, updated_path = update_source_by_path(
                                path_text=selected_path,
                                title=edited_title,
                                source_text=edited_text,
                                source_type=edited_source_type,
                                url=edited_url,
                                tags=edited_tags,
                            )

                            st.success(f"Source updated: {updated_path}")
                            st.warning("Rebuild chunk library after editing source text.")
                            st.rerun()

                        except Exception as error:
                            st.error("Source update failed.")
                            st.exception(error)

                with col_delete:
                    confirm_delete = st.checkbox(
                        "I understand this permanently deletes the selected source file.",
                        key=f"confirm_delete_{selected_source.source_id}",
                    )

                    if st.button("Delete Selected Source"):
                        if not confirm_delete:
                            st.warning("Tick the confirmation checkbox before deleting.")
                        else:
                            try:
                                deleted_path = delete_source_by_path(selected_path)
                                st.success(f"Deleted source: {deleted_path}")
                                st.warning("Rebuild chunk library after deleting sources.")
                                st.rerun()

                            except Exception as error:
                                st.error("Source deletion failed.")
                                st.exception(error)

            library_extraction_mode = st.radio(
                "Claim extraction mode for selected source:",
                ["OpenAI AI", "Local simple"],
                horizontal=True,
                key="library_extraction_mode",
            )

            library_analysis_mode = st.radio(
                "Claim analysis mode for selected source:",
                ["OpenAI AI", "Local rule-based"],
                horizontal=True,
                key="library_analysis_mode",
            )

            if st.button("Re-analyze Selected Source"):
                try:
                    extraction, rows, batch_path = run_article_pipeline(
                        source_title=selected_source.title,
                        article_text=selected_source.text,
                        extraction_mode=library_extraction_mode,
                        claim_analysis_mode=library_analysis_mode,
                    )

                    st.subheader("Extraction Summary")
                    st.write(extraction.extraction_summary)

                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True)

                    st.success(f"Batch report saved locally: {batch_path}")

                except Exception as error:
                    st.error("Source re-analysis failed.")
                    st.exception(error)


with tab_chunks:
    st.header("Chunk Search / RAG Prep")

    st.write(
        "This tab rebuilds searchable chunks from saved local sources. "
        "This is keyword-based retrieval for now. Vector embeddings come next."
    )

    existing_chunks = load_chunks()

    col_count, col_note = st.columns([1, 3])

    with col_count:
        st.metric("Current Chunks", len(existing_chunks))

    with col_note:
        st.info(
            "Chunks are stored locally in data/chunks/source_chunks.jsonl and ignored by Git."
        )

    st.subheader("Build / Rebuild Chunk Library")

    col_max, col_overlap = st.columns(2)

    with col_max:
        max_chars = st.number_input(
            "Max characters per chunk:",
            min_value=300,
            max_value=3000,
            value=1200,
            step=100,
        )

    with col_overlap:
        overlap_chars = st.number_input(
            "Overlap characters:",
            min_value=0,
            max_value=500,
            value=150,
            step=25,
        )

    if st.button("Rebuild Chunk Library"):
        try:
            chunk_count, chunk_path = rebuild_chunk_library(
                max_chars=int(max_chars),
                overlap_chars=int(overlap_chars),
            )

            st.success(f"Built {chunk_count} chunks.")
            st.info(f"Chunk file saved locally: {chunk_path}")

        except Exception as error:
            st.error("Chunk rebuild failed.")
            st.exception(error)

    st.subheader("Search Chunks")

    query = st.text_input(
        "Search saved chunks:",
        value="longevity",
        key="chunk_search_query",
    )

    limit = st.slider(
        "Maximum results:",
        min_value=1,
        max_value=25,
        value=10,
    )

    if st.button("Search Chunk Library"):
        try:
            results = search_chunks(query=query, limit=int(limit))

            if not results:
                st.warning("No chunks matched your search.")
            else:
                st.success(f"Found {len(results)} matching chunks.")

                rows = []
                for chunk in results:
                    rows.append(
                        {
                            "chunk_id": chunk.chunk_id,
                            "source_title": chunk.source_title,
                            "source_type": chunk.source_type,
                            "chunk_index": chunk.chunk_index,
                            "character_count": chunk.character_count,
                            "tags": ", ".join(chunk.tags),
                            "preview": chunk.text[:180],
                        }
                    )

                st.dataframe(pd.DataFrame(rows), use_container_width=True)

                st.subheader("Retrieved Chunk Details")

                for index, chunk in enumerate(results, start=1):
                    with st.expander(
                        f"{index}. {chunk.source_title} | chunk {chunk.chunk_index}"
                    ):
                        st.write("Chunk ID:", chunk.chunk_id)
                        st.write("Source ID:", chunk.source_id)
                        st.write("Source title:", chunk.source_title)
                        st.write("Source type:", chunk.source_type)
                        st.write("Source URL:", chunk.source_url or "None")
                        st.write("Tags:", ", ".join(chunk.tags) if chunk.tags else "None")
                        st.write("Character count:", chunk.character_count)
                        st.text_area(
                            "Chunk text:",
                            value=chunk.text,
                            height=240,
                            disabled=True,
                            key=f"chunk_text_{chunk.chunk_id}",
                        )

        except Exception as error:
            st.error("Chunk search failed.")
            st.exception(error)










with tab_vector:
    st.header("Vector Search / Semantic RAG")

    st.write(
        "This tab builds OpenAI embeddings for saved chunks and performs semantic search. "
        "This is the first real RAG layer."
    )

    embedding_records = load_embedding_records()

    col_count, col_model_note = st.columns([1, 3])

    with col_count:
        st.metric("Embedding Records", len(embedding_records))

    with col_model_note:
        st.info(
            "Embeddings are stored locally in data/embeddings/chunk_embeddings.jsonl and ignored by Git."
        )

    st.subheader("Build / Rebuild Embedding Store")

    st.warning(
        "This uses OpenAI API credits. Build chunks first in the Chunk Search / RAG Prep tab."
    )

    batch_size = st.number_input(
        "Embedding batch size:",
        min_value=1,
        max_value=100,
        value=50,
        step=5,
    )

    if st.button("Build Embeddings From Chunks"):
        try:
            count, path = build_embedding_store(batch_size=int(batch_size))
            st.success(f"Built {count} embedding records.")
            st.info(f"Embedding file saved locally: {path}")
            st.rerun()

        except Exception as error:
            st.error("Embedding build failed.")
            st.exception(error)

    st.subheader("Semantic Search")

    semantic_query = st.text_input(
        "Ask a semantic search question:",
        value="why do organisms age and how does longevity evolve?",
        key="semantic_search_query",
    )

    semantic_limit = st.slider(
        "Maximum semantic results:",
        min_value=1,
        max_value=20,
        value=5,
        key="semantic_search_limit",
    )

    if st.button("Run Semantic Search"):
        try:
            results = semantic_search(
                query=semantic_query,
                limit=int(semantic_limit),
            )

            if not results:
                st.warning(
                    "No embedding records found. Build chunks first, then build embeddings."
                )
            else:
                st.success(f"Found {len(results)} semantic matches.")

                rows = []
                for result in results:
                    rows.append(
                        {
                            "score": result["similarity_score"],
                            "source_title": result["source_title"],
                            "source_type": result["source_type"],
                            "chunk_index": result["chunk_index"],
                            "tags": ", ".join(result.get("tags", [])),
                            "preview": result["text"][:180],
                        }
                    )

                st.dataframe(pd.DataFrame(rows), use_container_width=True)

                st.subheader("Retrieved Semantic Context")

                for index, result in enumerate(results, start=1):
                    with st.expander(
                        f"{index}. Score {result['similarity_score']} | {result['source_title']} | chunk {result['chunk_index']}"
                    ):
                        st.write("Chunk ID:", result["chunk_id"])
                        st.write("Source ID:", result["source_id"])
                        st.write("Source title:", result["source_title"])
                        st.write("Source type:", result["source_type"])
                        st.write("Source URL:", result["source_url"] or "None")
                        st.write("Tags:", ", ".join(result.get("tags", [])) or "None")
                        st.write("Similarity score:", result["similarity_score"])

                        st.text_area(
                            "Retrieved text:",
                            value=result["text"],
                            height=260,
                            disabled=True,
                            key=f"semantic_chunk_{result['chunk_id']}",
                        )

        except Exception as error:
            st.error("Semantic search failed.")
            st.exception(error)
