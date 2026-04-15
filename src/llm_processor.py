from transformers import pipeline

bart_summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

t5_summarizer = pipeline(
    "summarization",
    model="t5-small"
)


def generate_summary_with_model(text, model_type="bart"):
    text = text.strip()

    if len(text) < 50:
        return text

    trimmed_text = text[:1000]
    input_words = len(trimmed_text.split())

    max_len = min(80, max(30, input_words // 2))
    min_len = min(40, max(15, input_words // 3))

    if model_type == "bart":
        summary = bart_summarizer(
            trimmed_text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )
    else:
        summary = t5_summarizer(
            "summarize: " + trimmed_text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )

    summary_text = summary[0]["summary_text"].strip()

    # Fix spacing like " ."
    summary_text = summary_text.replace(" .", ".").replace(" ,", ",").strip()

    # Capitalize first letter for cleaner formatting
    if summary_text:
        summary_text = summary_text[0].upper() + summary_text[1:]

    # Keep only complete sentence ending
    if "." in summary_text:
        summary_text = summary_text[:summary_text.rfind(".") + 1]

    return summary_text