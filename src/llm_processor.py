from functools import lru_cache

from transformers import pipeline


@lru_cache(maxsize=2)
def get_summarizer(model_type="bart"):
    if model_type == "bart":
        return pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )

    return pipeline(
        "summarization",
        model="t5-small"
    )


def generate_summary_with_model(text, model_type="bart"):
    text = text.strip()

    trimmed_text = text[:1000]
    input_words = len(trimmed_text.split())

    if input_words < 35:
        return clean_summary_text(trimmed_text)

    max_len = min(80, max(20, input_words // 2))
    min_len = min(max_len - 5, max(8, input_words // 4))

    if model_type == "bart":
        bart_summarizer = get_summarizer("bart")
        summary = bart_summarizer(
            trimmed_text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )
    else:
        t5_summarizer = get_summarizer("t5")
        summary = t5_summarizer(
            "summarize: " + trimmed_text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )

    summary_text = summary[0]["summary_text"].strip()
    return clean_summary_text(summary_text)


def clean_summary_text(summary_text):
    # Fix spacing like " ."
    summary_text = summary_text.replace(" .", ".").replace(" ,", ",").strip()

    # Capitalize first letter and sentence starts for cleaner formatting.
    if summary_text:
        summary_text = summary_text[0].upper() + summary_text[1:]
        summary_text = re_capitalize_sentences(summary_text)

    # Keep only complete sentence ending
    if "." in summary_text:
        summary_text = summary_text[:summary_text.rfind(".") + 1]

    return summary_text


def re_capitalize_sentences(text):
    parts = []
    for part in text.split(". "):
        part = part.strip()
        if part:
            part = part[0].upper() + part[1:]
        parts.append(part)
    return ". ".join(parts)
