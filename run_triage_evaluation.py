import csv
import json
from pathlib import Path

from src.parser import build_result


BASE_DIR = Path(__file__).resolve().parent
EVALUATION_DIR = BASE_DIR / "evaluation"
CASES_PATH = EVALUATION_DIR / "triage_cases.json"
REPORT_PATH = EVALUATION_DIR / "triage_evaluation_report.csv"
SUMMARY_PATH = EVALUATION_DIR / "triage_evaluation_summary.json"


def pass_fail(actual, expected):
    return actual == expected


def evaluate_case(case):
    result = build_result(case["text"], summary=case["text"])
    expected = case["expected"]

    checks = {
        "category_match": pass_fail(result["category"], expected["category"]),
        "priority_match": pass_fail(result["priority"], expected["priority"]),
        "urgency_match": pass_fail(result["urgency"], expected["urgency"]),
        "team_match": pass_fail(result["responsible_team"], expected["responsible_team"]),
        "review_flag_match": pass_fail(
            result["human_review"]["review_required"], expected["review_required"]
        ),
        "action_items_ok": len(result["action_items"]) >= expected["min_action_items"],
    }

    return {
        "case_id": case["id"],
        "expected_category": expected["category"],
        "actual_category": result["category"],
        "expected_priority": expected["priority"],
        "actual_priority": result["priority"],
        "expected_urgency": expected["urgency"],
        "actual_urgency": result["urgency"],
        "expected_team": expected["responsible_team"],
        "actual_team": result["responsible_team"],
        "expected_review_required": expected["review_required"],
        "actual_review_required": result["human_review"]["review_required"],
        "expected_min_action_items": expected["min_action_items"],
        "actual_action_items": len(result["action_items"]),
        "validation_score": result["validation"]["validation_score"],
        **checks,
    }


def accuracy(rows, field):
    return round(sum(1 for row in rows if row[field]) / len(rows) * 100, 1)


def main():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    rows = [evaluate_case(case) for case in cases]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "total_cases": len(rows),
        "category_accuracy_percent": accuracy(rows, "category_match"),
        "priority_accuracy_percent": accuracy(rows, "priority_match"),
        "urgency_accuracy_percent": accuracy(rows, "urgency_match"),
        "responsible_team_accuracy_percent": accuracy(rows, "team_match"),
        "review_flag_accuracy_percent": accuracy(rows, "review_flag_match"),
        "action_item_detection_percent": accuracy(rows, "action_items_ok"),
        "average_validation_score": round(
            sum(row["validation_score"] for row in rows) / len(rows), 1
        ),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Triage evaluation complete")
    print(f"Cases tested: {summary['total_cases']}")
    print(f"Category accuracy: {summary['category_accuracy_percent']}%")
    print(f"Priority accuracy: {summary['priority_accuracy_percent']}%")
    print(f"Urgency accuracy: {summary['urgency_accuracy_percent']}%")
    print(f"Team routing accuracy: {summary['responsible_team_accuracy_percent']}%")
    print(f"Review flag accuracy: {summary['review_flag_accuracy_percent']}%")
    print(f"Action-item detection: {summary['action_item_detection_percent']}%")
    print(f"Average validation score: {summary['average_validation_score']}/100")
    print(f"Saved: {REPORT_PATH.relative_to(BASE_DIR)}")
    print(f"Saved: {SUMMARY_PATH.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
