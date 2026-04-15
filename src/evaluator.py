import re


def count_repeated_words(words):
    repeated = 0

    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            repeated += 1

    return repeated


def evaluate_summary(summary_text):
    summary = summary_text.strip()
    words = summary.split()

    word_count = len(words)
    ends_well = summary.endswith(".")
    too_short = word_count < 8
    too_long = word_count > 45
    has_capital_start = summary[0].isupper() if summary else False
    awkward_spacing = " ." in summary or " ," in summary
    repeated_words = count_repeated_words([w.lower() for w in words])

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

    return {
        "word_count": word_count,
        "ends_well": ends_well,
        "too_short": too_short,
        "too_long": too_long,
        "has_capital_start": has_capital_start,
        "awkward_spacing": awkward_spacing,
        "repeated_words": repeated_words,
        "score": score
    }


def compare_summaries(bart_summary, t5_summary):
    bart_eval = evaluate_summary(bart_summary)
    t5_eval = evaluate_summary(t5_summary)

    if bart_eval["score"] > t5_eval["score"]:
        preferred_model = "BART"
    elif t5_eval["score"] > bart_eval["score"]:
        preferred_model = "T5"
    else:
        preferred_model = "Tie"

    return {
        "bart_evaluation": bart_eval,
        "t5_evaluation": t5_eval,
        "preferred_model": preferred_model
    }