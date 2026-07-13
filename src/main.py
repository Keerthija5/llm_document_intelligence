import sys
import os
from time import perf_counter

sys.path.append(os.path.dirname(__file__))

from file_handler import read_text_files_from_folder
from llm_processor import generate_summary_with_model
from parser import build_result
from exporter import save_json_output, save_csv_output
from evaluator import compare_summaries
from workflow_log import (
    append_run_log,
    assess_routing_confidence,
    build_document_hash,
    build_processing_id,
    find_duplicate_hashes,
)


def main():
    print("LLM-Powered Document Intelligence System")
    print("-" * 50)

    input_folder = os.path.join("data", "input")
    output_folder = os.path.join("data", "output")

    os.makedirs(output_folder, exist_ok=True)

    documents = read_text_files_from_folder(input_folder)

    if not documents:
        print("No .txt files found inside data/input/")
        return

    all_results = []
    processed_results = []
    duplicate_hashes = find_duplicate_hashes(documents)

    for file_name, text in documents:
        print(f"\nProcessing: {file_name}")

        try:
            start_time = perf_counter()
            document_hash = build_document_hash(text)
            summary_bart = generate_summary_with_model(text, "bart")
            summary_t5 = generate_summary_with_model(text, "t5")

            result = build_result(text, summary_bart)
            duplicate = document_hash in duplicate_hashes
            if duplicate:
                result["workflow_status"] = "Duplicate detected"
                result["human_review"]["review_required"] = True
                result["human_review"]["reasons"].append("Duplicate document detected")
            result["file_name"] = file_name
            result["processing_id"] = build_processing_id(file_name, document_hash)
            result["document_hash"] = document_hash
            result["duplicate"] = duplicate
            result["routing"] = assess_routing_confidence(result)
            result["processing_latency_ms"] = round((perf_counter() - start_time) * 1000, 2)
            result["bart_summary"] = summary_bart
            result["t5_summary"] = summary_t5
            result["models_used"] = ["BART", "T5"]

            evaluation = compare_summaries(summary_bart, summary_t5, text, result["action_items"])
            result["evaluation"] = evaluation

            save_json_output(file_name, result, output_folder)
            processed_results.append(result)

            all_results.append({
                "file_name": file_name,
                "bart_summary": result["bart_summary"],
                "t5_summary": result["t5_summary"],
                "preferred_model": evaluation["preferred_model"],
                "bart_score": evaluation["bart_evaluation"]["score"],
                "t5_score": evaluation["t5_evaluation"]["score"],
                "action_items": " | ".join(result["action_items"]),
                "category": result["category"],
                "priority": result["priority"],
                "urgency": result["urgency"],
                "responsible_team": result["responsible_team"],
                "involved_teams": " | ".join(result["involved_teams"]),
                "workflow_status": result["workflow_status"],
                "routing_confidence": result["routing"]["overall"],
                "duplicate": result["duplicate"],
                "business_impact": result["business_impact"],
                "deadlines": " | ".join(result["deadlines"]),
                "risks": ", ".join(result["risks"]),
                "sentiment": result["sentiment"],
                "validation_score": result["validation"]["validation_score"],
                "human_review_required": result["human_review"]["review_required"],
                "review_reasons": " | ".join(result["human_review"]["reasons"]),
                "recommended_next_action": result["recommended_next_action"],
                "preferred_reason": evaluation["preferred_reason"],
                "keywords": ", ".join(result["keywords"]),
                "processing_id": result["processing_id"],
                "document_hash": result["document_hash"],
                "processing_latency_ms": result["processing_latency_ms"],
            })

            print("Done")

        except Exception as error:
            print(f"Error while processing {file_name}: {error}")

    if all_results:
        save_csv_output(all_results, output_folder)
        append_run_log(processed_results)
        print(f"\nFinished. Outputs saved in: {output_folder}")
    else:
        print("\nNo results were saved.")


if __name__ == "__main__":
    main()
