import re


def count_repeated_words(words):
    repeated = 0

    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            repeated += 1

    return repeated


def extract_terms(text):
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this", "into", "using",
        "are", "was", "were", "has", "have", "should", "need", "needs", "team",
        "there", "their", "about", "before", "after", "during",
    }
    return {
        word.lower()
        for word in re.findall(r"\b[a-zA-Z]{4,}\b", text)
        if word.lower() not in stop_words
    }


def score_coverage(summary_text, reference_terms):
    summary_terms = extract_terms(summary_text)
    if not reference_terms:
        return 0
    return round(len(summary_terms & reference_terms) / len(reference_terms) * 100)


def evaluate_summary(summary_text, source_text="", action_items=None):
    summary = summary_text.strip()
    words = summary.split()
    action_items = action_items or []
    source_terms = extract_terms(source_text)

    word_count = len(words)
    ends_well = summary.endswith(".")
    too_short = word_count < 8
    too_long = word_count > 45
    has_capital_start = summary[0].isupper() if summary else False
    awkward_spacing = " ." in summary or " ," in summary
    repeated_words = count_repeated_words([w.lower() for w in words])
    keyword_coverage = score_coverage(summary, set(list(source_terms)[:12]))
    action_item_coverage = score_coverage(summary, extract_terms(" ".join(action_items))) if action_items else 100

    score = 0

    if has_capital_start:
        score += 1

    if ends_well:
        score += 1

    if not too_short:
        score += 1

    if not too_long:
        score += 1

    if not awkward_spacing:
        score += 1

    if repeated_words == 0:
        score += 1

    if keyword_coverage >= 25:
        score += 1

    if action_item_coverage >= 25:
        score += 1

    return {
        "word_count": word_count,
        "ends_well": ends_well,
        "too_short": too_short,
        "too_long": too_long,
        "has_capital_start": has_capital_start,
        "awkward_spacing": awkward_spacing,
        "repeated_words": repeated_words,
        "keyword_coverage": keyword_coverage,
        "action_item_coverage": action_item_coverage,
        "score": score
    }


def compare_summaries(bart_summary, t5_summary, source_text="", action_items=None):
    bart_eval = evaluate_summary(bart_summary, source_text, action_items)
    t5_eval = evaluate_summary(t5_summary, source_text, action_items)

    if bart_eval["score"] > t5_eval["score"]:
        preferred_model = "BART"
    elif t5_eval["score"] > bart_eval["score"]:
        preferred_model = "T5"
    else:
        preferred_model = "Tie"

    preferred_reason = build_preferred_reason(preferred_model, bart_eval, t5_eval)

    return {
        "bart_evaluation": bart_eval,
        "t5_evaluation": t5_eval,
        "preferred_model": preferred_model,
        "preferred_reason": preferred_reason,
    }


def build_preferred_reason(preferred_model, bart_eval, t5_eval):
    if preferred_model == "Tie":
        return "Both summaries received the same evaluation score."

    selected = bart_eval if preferred_model == "BART" else t5_eval
    other = t5_eval if preferred_model == "BART" else bart_eval
    reasons = []

    if selected["keyword_coverage"] > other["keyword_coverage"]:
        reasons.append("better keyword coverage")
    if selected["action_item_coverage"] > other["action_item_coverage"]:
        reasons.append("better action-item coverage")
    if selected["repeated_words"] < other["repeated_words"]:
        reasons.append("less repetition")
    if not selected["too_short"] and not selected["too_long"]:
        reasons.append("better summary length")

    if not reasons:
        reasons.append("higher overall formatting and quality score")

    return f"{preferred_model} selected due to " + ", ".join(reasons) + "."
