import sys
import os

sys.path.append(os.path.dirname(__file__))

from file_handler import read_text_files_from_folder
from llm_processor import generate_summary_with_model
from parser import build_result
from exporter import save_json_output, save_csv_output
from evaluator import compare_summaries


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

    for file_name, text in documents:
        print(f"\nProcessing: {file_name}")

        try:
            summary_bart = generate_summary_with_model(text, "bart")
            summary_t5 = generate_summary_with_model(text, "t5")

            result = build_result(text, summary_bart)
            result["bart_summary"] = summary_bart
            result["t5_summary"] = summary_t5
            result["models_used"] = ["BART", "T5"]

            evaluation = compare_summaries(summary_bart, summary_t5)
            result["evaluation"] = evaluation

            save_json_output(file_name, result, output_folder)

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
                "keywords": ", ".join(result["keywords"])
            })

            print("Done")

        except Exception as error:
            print(f"Error while processing {file_name}: {error}")

    if all_results:
        save_csv_output(all_results, output_folder)
        print(f"\nFinished. Outputs saved in: {output_folder}")
    else:
        print("\nNo results were saved.")


if __name__ == "__main__":
    main()