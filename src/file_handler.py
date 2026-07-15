import os


SUPPORTED_TEXT_EXTENSIONS = (".txt", ".md", ".eml")


def read_text_files_from_folder(folder_path):
    documents = []

    if not os.path.exists(folder_path):
        return documents

    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(SUPPORTED_TEXT_EXTENSIONS):
            full_path = os.path.join(folder_path, file_name)

            try:
                with open(full_path, "r", encoding="utf-8") as file:
                    text = file.read().strip()
            except UnicodeDecodeError:
                with open(full_path, "r", encoding="latin-1") as file:
                    text = file.read().strip()

            if text:
                documents.append((file_name, text))

    return documents
