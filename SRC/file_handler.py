import os


def read_text_files_from_folder(folder_path):
    documents = []

    if not os.path.exists(folder_path):
        return documents

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            full_path = os.path.join(folder_path, file_name)

            with open(full_path, "r", encoding="utf-8") as file:
                text = file.read().strip()

            if text:
                documents.append((file_name, text))

    return documents