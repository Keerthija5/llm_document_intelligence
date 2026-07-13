from __future__ import annotations

from datetime import datetime, timezone
import csv
import hashlib
from pathlib import Path


LOG_COLUMNS = [
    "processed_at",
    "processing_id",
    "file_name",
    "document_hash",
    "duplicate",
    "category",
    "priority",
    "urgency",
    "responsible_team",
    "routing_confidence",
    "workflow_status",
    "review_required",
    "review_reasons",
    "validation_score",
    "preferred_model",
    "processing_latency_ms",
]


def build_document_hash(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def build_processing_id(file_name: str, document_hash: str) -> str:
    seed = f"{file_name}:{document_hash}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def find_duplicate_hashes(documents: list[tuple[str, str]]) -> set[str]:
    counts: dict[str, int] = {}
    for _file_name, text in documents:
        document_hash = build_document_hash(text)
        counts[document_hash] = counts.get(document_hash, 0) + 1
    return {document_hash for document_hash, count in counts.items() if count > 1}


def assess_routing_confidence(result: dict) -> dict:
    evidence = {
        "category": result.get("keywords", [])[:3],
        "responsible_team": result.get("involved_teams", []),
        "priority": result.get("risks", []) + result.get("deadlines", []),
    }
    score = 0
    if result.get("category") != "General Document":
        score += 1
    if result.get("responsible_team") != "Not clearly identified":
        score += 1
    if result.get("risks") or result.get("deadlines") or result.get("action_items"):
        score += 1

    if score >= 3:
        overall = "High"
    elif score == 2:
        overall = "Medium"
    else:
        overall = "Low"

    return {
        "overall": overall,
        "evidence": evidence,
    }


def append_run_log(results: list[dict], output_path: str | Path = "data/output/triage_run_log.csv") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for result in results:
            writer.writerow(_build_log_row(result))
    return path


def _build_log_row(result: dict) -> dict:
    human_review = result.get("human_review", {})
    validation = result.get("validation", {})
    routing = result.get("routing", {})
    return {
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "processing_id": result.get("processing_id", ""),
        "file_name": result.get("file_name", ""),
        "document_hash": result.get("document_hash", ""),
        "duplicate": result.get("duplicate", False),
        "category": result.get("category", ""),
        "priority": result.get("priority", ""),
        "urgency": result.get("urgency", ""),
        "responsible_team": result.get("responsible_team", ""),
        "routing_confidence": routing.get("overall", ""),
        "workflow_status": result.get("workflow_status", ""),
        "review_required": human_review.get("review_required", False),
        "review_reasons": " | ".join(human_review.get("reasons", [])),
        "validation_score": validation.get("validation_score", ""),
        "preferred_model": result.get("preferred_model", ""),
        "processing_latency_ms": result.get("processing_latency_ms", ""),
    }
