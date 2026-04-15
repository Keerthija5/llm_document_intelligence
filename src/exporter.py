import os
import json
import pandas as pd


def save_json_output(file_name, result, output_folder):
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(output_folder, f"{base_name}.json")

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)


def save_csv_output(results, output_folder):
    df = pd.DataFrame(results)
    output_path = os.path.join(output_folder, "all_results.csv")
    df.to_csv(output_path, index=False)