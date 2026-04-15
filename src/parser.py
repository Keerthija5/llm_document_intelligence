import re
from collections import Counter


def extract_action_items(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    action_items = []

    action_keywords = [
        "should", "need to", "must", "please", "review",
        "check", "inspect", "prepare", "analyze", "schedule",
        "update", "share", "evaluate", "identify"
    ]

    for sentence in sentences:
        sentence_clean = sentence.strip()
        sentence_lower = sentence_clean.lower()

        for keyword in action_keywords:
            if keyword in sentence_lower:
                if len(sentence_clean.split()) > 5:
                    action_items.append(sentence_clean)
                break

    return action_items


def detect_category(text):
    text_lower = text.lower()

    if "meeting" in text_lower or "discussed" in text_lower:
        return "Meeting Notes"
    if "ticket" in text_lower or "complaint" in text_lower or "issue" in text_lower or "fault" in text_lower:
        return "Support Ticket"
    if "email" in text_lower:
        return "Email"
    if "request" in text_lower or "please" in text_lower:
        return "Task Request"
    if "report" in text_lower:
        return "Report"

    return "General Document"


def detect_priority(text):
    text_lower = text.lower()

    high_words = ["urgent", "immediately", "critical", "asap", "high priority", "failure"]
    medium_words = ["soon", "important", "by tomorrow", "this week"]

    for word in high_words:
        if word in text_lower:
            return "High"

    for word in medium_words:
        if word in text_lower:
            return "Medium"

    return "Low"


def detect_urgency(text):
    text_lower = text.lower()

    urgent_words = ["urgent", "immediately", "asap", "by tomorrow", "critical"]
    moderate_words = ["soon", "this week", "next week", "important"]

    for word in urgent_words:
        if word in text_lower:
            return "Urgent"

    for word in moderate_words:
        if word in text_lower:
            return "Moderate"

    return "Low"


def extract_keywords(text, top_n=5):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

    stop_words = {
        "this", "that", "with", "from", "have", "will", "should", "needs",
        "team", "teams", "there", "about", "being", "their", "before",
        "after", "during", "today", "tomorrow", "week", "short",
        "reported", "repeated", "different", "using"
    }

    filtered_words = [word for word in words if word not in stop_words]

    counts = Counter(filtered_words)

    keywords = []
    for word, count in counts.most_common():
        keywords.append(word)
        if len(keywords) == top_n:
            break

    return keywords


def build_result(text, summary):
    return {
        "summary": summary,
        "action_items": extract_action_items(text),
        "category": detect_category(text),
        "priority": detect_priority(text),
        "urgency": detect_urgency(text),
        "keywords": extract_keywords(text)
    }