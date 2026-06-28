from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from evaluator import compare_summaries
from llm_processor import generate_summary_with_model
from parser import build_result


st.set_page_config(
    page_title="LLM Document Triage",
    page_icon="",
    layout="wide",
)


def process_document(file_name: str, text: str) -> dict:
    bart_summary = generate_summary_with_model(text, "bart")
    t5_summary = generate_summary_with_model(text, "t5")

    result = build_result(text, bart_summary)
    evaluation = compare_summaries(bart_summary, t5_summary, text, result["action_items"])

    result.update(
        {
            "file_name": file_name,
            "bart_summary": bart_summary,
            "t5_summary": t5_summary,
            "preferred_model": evaluation["preferred_model"],
            "preferred_reason": evaluation["preferred_reason"],
            "bart_score": evaluation["bart_evaluation"]["score"],
            "t5_score": evaluation["t5_evaluation"]["score"],
            "evaluation": evaluation,
        }
    )
    return result


def decode_uploaded_file(uploaded_file) -> str:
    file_bytes = uploaded_file.getvalue()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return file_bytes.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore").strip()


def build_table(results: list[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "file_name": result["file_name"],
                "category": result["category"],
                "priority": result["priority"],
                "urgency": result["urgency"],
                "responsible_team": result["responsible_team"],
                "involved_teams": " | ".join(result["involved_teams"]),
                "workflow_status": result["workflow_status"],
                "business_impact": result["business_impact"],
                "review_required": result["human_review"]["review_required"],
                "validation_score": result["validation"]["validation_score"],
                "preferred_model": result["preferred_model"],
                "deadlines": " | ".join(result["deadlines"]),
                "risks": ", ".join(result["risks"]),
                "recommended_next_action": result["recommended_next_action"],
            }
        )
    return pd.DataFrame(rows)


def results_to_json(results: list[dict]) -> str:
    return json.dumps(results, indent=4)


def results_to_csv(results: list[dict]) -> str:
    return build_table(results).to_csv(index=False)


st.title("LLM-Based Business Document Triage Dashboard")
st.caption(
    "Compare BART and T5 summaries, extract structured business fields, flag documents for review, "
    "and export JSON/CSV outputs."
)
st.info("First processing can take longer because the BART and T5 models load locally. Short alerts are handled safely without forcing long model summaries.")

uploaded_files = st.file_uploader(
    "Upload business documents",
    type=["txt", "md", "eml"],
    accept_multiple_files=True,
)

sample_text = st.text_area(
    "Or paste one document or email",
    height=180,
    placeholder="Paste a support ticket, maintenance report, meeting note, project update, or email text here...",
)

if "results" not in st.session_state:
    st.session_state.results = []

if st.button("Process documents", type="primary"):
    documents = []

    for uploaded_file in uploaded_files or []:
        text = decode_uploaded_file(uploaded_file)
        if text:
            documents.append((uploaded_file.name, text))

    if sample_text.strip():
        documents.append(("pasted_document.txt", sample_text.strip()))

    if not documents:
        st.warning("Upload at least one text file or paste a document.")
    else:
        results = []
        progress = st.progress(0)
        for index, (file_name, text) in enumerate(documents, start=1):
            with st.spinner(f"Processing {file_name}..."):
                results.append(process_document(file_name, text))
            progress.progress(index / len(documents))
        st.session_state.results = results
        st.success(f"Processed {len(results)} document(s).")


results = st.session_state.results

if results:
    table = build_table(results)

    total_documents = len(results)
    review_count = int(table["review_required"].sum())
    high_priority_count = int((table["priority"] == "High").sum())
    average_validation = round(table["validation_score"].mean())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents", total_documents)
    c2.metric("Human review", review_count)
    c3.metric("High priority", high_priority_count)
    c4.metric("Avg validation", f"{average_validation}/100")

    st.markdown("### Batch Triage Table")
    st.dataframe(table, use_container_width=True, hide_index=True)

    selected_file = st.selectbox("Review one document", [result["file_name"] for result in results])
    selected = next(result for result in results if result["file_name"] == selected_file)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### BART Summary")
        st.write(selected["bart_summary"])
        st.markdown("### T5 Summary")
        st.write(selected["t5_summary"])

    with col2:
        st.markdown("### Structured Extraction")
        st.json(
            {
                "category": selected["category"],
                "priority": selected["priority"],
                "urgency": selected["urgency"],
                "responsible_team": selected["responsible_team"],
                "involved_teams": selected["involved_teams"],
                "email_metadata": selected["email_metadata"],
                "deadlines": selected["deadlines"],
                "risks": selected["risks"],
                "sentiment": selected["sentiment"],
                "workflow_status": selected["workflow_status"],
                "business_impact": selected["business_impact"],
                "action_items": selected["action_items"],
                "recommended_next_action": selected["recommended_next_action"],
            }
        )

    st.markdown("### Model Evaluation")
    e1, e2, e3 = st.columns(3)
    e1.metric("Preferred model", selected["preferred_model"])
    e2.metric("BART score", selected["bart_score"])
    e3.metric("T5 score", selected["t5_score"])
    st.info(selected["preferred_reason"])

    st.markdown("### Output Validation")
    v1, v2 = st.columns([1, 3])
    v1.metric("Validation score", f"{selected['validation']['validation_score']}/100")
    if selected["human_review"]["review_required"]:
        v2.warning("Human review required: " + ", ".join(selected["human_review"]["reasons"]))
    else:
        v2.success("No immediate human-review flag.")

    st.download_button(
        "Download JSON results",
        data=results_to_json(results),
        file_name="document_triage_results.json",
        mime="application/json",
    )
    st.download_button(
        "Download CSV table",
        data=results_to_csv(results),
        file_name="document_triage_results.csv",
        mime="text/csv",
    )
