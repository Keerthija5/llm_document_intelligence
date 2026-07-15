from __future__ import annotations

import json
from pathlib import Path
import sys
from time import perf_counter

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from evaluator import compare_summaries
from llm_processor import generate_summary_with_model
from parser import build_result
from workflow_log import (
    apply_routing_review_flag,
    append_run_log,
    assess_routing_confidence,
    build_document_hash,
    build_processing_id,
    find_duplicate_hashes,
)


PRIORITY_SCORE = {"High": 3, "Medium": 2, "Low": 1}
URGENCY_SCORE = {"Urgent": 3, "Moderate": 2, "Low": 1}
ROUTING_REVIEW_SCORE = {"Low": 3, "Medium": 2, "High": 1}


st.set_page_config(
    page_title="LLM Document Triage",
    page_icon="",
    layout="wide",
)


def process_document(file_name: str, text: str, duplicate_hashes: set[str]) -> dict:
    start_time = perf_counter()
    document_hash = build_document_hash(text)
    bart_summary = generate_summary_with_model(text, "bart")
    t5_summary = generate_summary_with_model(text, "t5")

    result = build_result(text, bart_summary)
    evaluation = compare_summaries(bart_summary, t5_summary, text, result["action_items"])
    processing_latency_ms = round((perf_counter() - start_time) * 1000, 2)
    routing = assess_routing_confidence(result)
    result["routing"] = routing
    apply_routing_review_flag(result)
    duplicate = document_hash in duplicate_hashes
    if duplicate:
        result["workflow_status"] = "Duplicate detected"
        result["human_review"]["review_required"] = True
        if "Duplicate document detected" not in result["human_review"]["reasons"]:
            result["human_review"]["reasons"].append("Duplicate document detected")

    result.update(
        {
            "file_name": file_name,
            "processing_id": build_processing_id(file_name, document_hash),
            "document_hash": document_hash,
            "duplicate": duplicate,
            "processing_latency_ms": processing_latency_ms,
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
                "routing_confidence": result["routing"]["overall"],
                "duplicate": result["duplicate"],
                "business_impact": result["business_impact"],
                "review_required": result["human_review"]["review_required"],
                "validation_score": result["validation"]["validation_score"],
                "preferred_model": result["preferred_model"],
                "deadlines": " | ".join(result["deadlines"]),
                "risks": ", ".join(result["risks"]),
                "recommended_next_action": result["recommended_next_action"],
                "processing_latency_ms": result["processing_latency_ms"],
                "queue_score": calculate_queue_score(result),
            }
        )
    return pd.DataFrame(rows)


def calculate_queue_score(result: dict) -> int:
    score = 0
    if result["human_review"]["review_required"]:
        score += 5
    if result.get("duplicate"):
        score += 2
    score += PRIORITY_SCORE.get(result.get("priority"), 0)
    score += URGENCY_SCORE.get(result.get("urgency"), 0)
    score += ROUTING_REVIEW_SCORE.get(result.get("routing", {}).get("overall"), 0)
    return score


def sort_triage_queue(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return table
    return table.sort_values(
        by=["review_required", "queue_score", "processing_latency_ms"],
        ascending=[False, False, False],
    )


def summarize_review_reasons(results: list[dict]) -> pd.DataFrame:
    reasons = [
        reason
        for result in results
        for reason in result["human_review"]["reasons"]
    ]
    if not reasons:
        return pd.DataFrame(columns=["reason", "count"])
    return pd.Series(reasons, name="reason").value_counts().reset_index(name="count")


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
        duplicate_hashes = find_duplicate_hashes(documents)
        for index, (file_name, text) in enumerate(documents, start=1):
            with st.spinner(f"Processing {file_name}..."):
                results.append(process_document(file_name, text, duplicate_hashes))
            progress.progress(index / len(documents))
        log_path = append_run_log(results)
        st.session_state.results = results
        st.session_state.log_path = str(log_path)
        st.success(f"Processed {len(results)} document(s).")


results = st.session_state.results

if results:
    table = build_table(results)
    queue_table = sort_triage_queue(table)

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
    st.caption("Queue monitoring")
    f1, f2, f3 = st.columns(3)
    review_only = f1.toggle("Show review queue only", value=False)
    category_options = ["All"] + sorted(table["category"].dropna().unique().tolist())
    team_options = ["All"] + sorted(table["responsible_team"].dropna().unique().tolist())
    selected_category = f2.selectbox("Category", category_options)
    selected_team = f3.selectbox("Responsible team", team_options)

    display_table = queue_table.copy()
    if review_only:
        display_table = display_table[display_table["review_required"]]
    if selected_category != "All":
        display_table = display_table[display_table["category"] == selected_category]
    if selected_team != "All":
        display_table = display_table[display_table["responsible_team"] == selected_team]

    st.dataframe(display_table, use_container_width=True, hide_index=True)
    if st.session_state.get("log_path"):
        st.caption(f"Run log saved locally: {st.session_state.log_path}")

    with st.expander("Batch summary"):
        s1, s2, s3 = st.columns(3)
        s1.markdown("**Categories**")
        s1.dataframe(table["category"].value_counts().reset_index(name="count"), hide_index=True)
        s2.markdown("**Responsible teams**")
        s2.dataframe(table["responsible_team"].value_counts().reset_index(name="count"), hide_index=True)
        s3.markdown("**Review reasons**")
        s3.dataframe(summarize_review_reasons(results), hide_index=True)

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
                "routing": selected["routing"],
                "duplicate": selected["duplicate"],
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

    st.markdown("### Routing Confidence")
    st.metric("Overall", selected["routing"]["overall"])
    st.json(selected["routing"]["evidence"])
    st.caption("Routing checks")
    st.json(selected["routing"]["checks"])

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
