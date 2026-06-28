import re
from collections import Counter


def contains_keyword(text_lower, keyword):
    if " " in keyword:
        return keyword in text_lower
    return re.search(rf"\b{re.escape(keyword)}\b", text_lower) is not None


def is_job_rejection(text_lower):
    rejection_phrases = [
        "move forward with other candidates",
        "move forward with other applicants",
        "pursue other candidates",
        "pursue other applicants",
        "chosen to pursue other applicants",
        "decided to move forward with other candidates",
        "unable to shortlist",
        "unable to move forward",
        "unable to provide individual feedback",
        "not selected",
        "regret to inform you",
        "we regret to inform",
        "decision does not reflect negatively",
    ]
    return any(phrase in text_lower for phrase in rejection_phrases)


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

        if "don't let this stop you" in sentence_lower or "do not let this stop you" in sentence_lower:
            continue

        for keyword in action_keywords:
            if contains_keyword(sentence_lower, keyword):
                if len(sentence_clean.split()) > 5:
                    action_items.append(sentence_clean)
                break

    return action_items


def detect_responsible_team(text):
    text_lower = text.lower()
    category = detect_category(text)
    category_owner = {
        "Job Alert / Career Opportunity": "Career Tracking",
        "Job Application Rejection": "Career Tracking",
        "Job Application Update": "Career Tracking",
        "Interview Invitation": "Career Tracking",
        "Marketing / Promotion": "Personal Review",
        "Event / Ticket Alert": "Personal Review",
        "Reminder": "Personal Review",
        "Schedule / Timetable": "Personal Review",
        "Personal Message": "Personal Review",
    }
    if category in category_owner:
        return category_owner[category]

    team_keywords = {
        "Maintenance": ["maintenance", "inspect", "repair", "unit", "equipment", "fault"],
        "Engineering": ["engineering", "root cause", "technical", "design", "system"],
        "Operations": ["operations", "production", "shift", "workflow", "process"],
        "Customer Support": ["customer", "complaint", "ticket", "support", "service"],
        "Recruitment / HR": ["candidate", "application", "interview", "hiring", "recruitment", "career", "role"],
        "Process Improvement": ["process improvement", "standard template", "review time", "efficiency"],
        "Management": ["manager", "stakeholder", "leadership", "approval", "decision"],
    }

    matches = []
    for team, keywords in team_keywords.items():
        score = sum(1 for keyword in keywords if contains_keyword(text_lower, keyword))
        if score:
            matches.append((team, score))

    if not matches:
        return "Not clearly identified"

    matches.sort(key=lambda item: item[1], reverse=True)
    return matches[0][0]


def detect_involved_teams(text):
    text_lower = text.lower()
    category = detect_category(text)
    if category in {
        "Job Alert / Career Opportunity",
        "Job Application Rejection",
        "Job Application Update",
        "Interview Invitation",
    }:
        return ["Career Tracking"]
    if category in {"Marketing / Promotion", "Event / Ticket Alert", "Reminder", "Schedule / Timetable", "Personal Message"}:
        return ["Personal Review"]

    team_keywords = {
        "Maintenance": ["maintenance", "inspect", "repair", "unit", "equipment", "fault"],
        "Engineering": ["engineering", "root cause", "technical", "design", "system"],
        "Operations": ["operations", "production", "shift", "workflow", "process"],
        "Customer Support": ["customer", "complaint", "ticket", "support", "service"],
        "Recruitment / HR": ["candidate", "application", "interview", "hiring", "recruitment", "career", "role"],
        "Process Improvement": ["process improvement", "standard template", "review time", "efficiency"],
        "Management": ["manager", "stakeholder", "leadership", "approval", "decision"],
    }

    matches = []
    for team, keywords in team_keywords.items():
        score = sum(1 for keyword in keywords if contains_keyword(text_lower, keyword))
        if score:
            matches.append((team, score))

    matches.sort(key=lambda item: item[1], reverse=True)
    return [team for team, _ in matches]


def extract_deadlines(text):
    patterns = [
        r"\bby tomorrow(?: morning| evening)?\b",
        r"\bby friday\b",
        r"\bby monday\b",
        r"\bby tuesday\b",
        r"\bby wednesday\b",
        r"\bby thursday\b",
        r"\bby next week\b",
        r"\bthis week\b",
        r"\bnext week\b",
        r"\bbefore the next [a-z\s]+",
        r"\bas soon as possible\b",
        r"\basap\b",
    ]
    found = []
    for pattern in patterns:
        found.extend(match.group(0) for match in re.finditer(pattern, text, flags=re.IGNORECASE))
    return list(dict.fromkeys(item.strip() for item in found))


def extract_risk_indicators(text):
    text_lower = text.lower()
    risk_patterns = {
        "fault": ["fault", "faults"],
        "failure": ["failure", "failures"],
        "delay": ["delay", "delays", "delayed"],
        "complaint": ["complaint", "complaints"],
        "critical": ["critical"],
        "urgent": ["urgent"],
        "blocked": ["blocked"],
        "outage": ["outage"],
        "safety": ["safety"],
        "production stop": ["production stopped", "line stopped"],
        "confusion": ["confusion"],
        "inconsistent format": ["inconsistent", "different formats"],
        "missing information": ["missing"],
        "root cause": ["root cause"],
        "high priority": ["high priority"],
    }
    risks = []
    for label, patterns in risk_patterns.items():
        if any(contains_keyword(text_lower, pattern) for pattern in patterns):
            risks.append(label)
    return risks


def detect_sentiment(text):
    text_lower = text.lower()
    negative_terms = [
        "fault", "failure", "delay", "complaint", "urgent", "critical",
        "blocked", "confusion", "outage", "dissatisfied"
    ]
    positive_terms = ["improved", "completed", "resolved", "approved", "successful", "stable"]
    if is_job_rejection(text_lower):
        return "Negative / Rejection"

    negative_score = sum(1 for term in negative_terms if contains_keyword(text_lower, term))
    positive_score = sum(1 for term in positive_terms if contains_keyword(text_lower, term))

    if negative_score > positive_score:
        return "Concern / Issue"
    if positive_score > negative_score:
        return "Positive / Stable"
    return "Neutral"


def detect_category(text):
    text_lower = text.lower()

    if (
        "new job ad" in text_lower
        or "job alert" in text_lower
        or "search alert" in text_lower
        or ("new job" in text_lower and ("machine learning" in text_lower or "data science" in text_lower or "engineer" in text_lower))
    ):
        return "Job Alert / Career Opportunity"
    if is_job_rejection(text_lower):
        return "Job Application Rejection"
    if "interview" in text_lower and ("schedule" in text_lower or "invite" in text_lower or "invitation" in text_lower):
        return "Interview Invitation"
    if "congratulations" in text_lower and ("offer" in text_lower or "selected" in text_lower or "interview" in text_lower):
        return "Job Application Update"
    if "unsubscribe" in text_lower or "limited time offer" in text_lower or "promotion" in text_lower or "discount" in text_lower:
        return "Marketing / Promotion"
    if "ticket" in text_lower and ("concert" in text_lower or "event" in text_lower or "available" in text_lower):
        return "Event / Ticket Alert"
    if "reminder" in text_lower or "don't forget" in text_lower or "do not forget" in text_lower:
        return "Reminder"
    if "timetable" in text_lower or "schedule for the week" in text_lower or "weekly schedule" in text_lower:
        return "Schedule / Timetable"
    if "good morning" in text_lower or "good night" in text_lower:
        return "Personal Message"
    if "meeting" in text_lower or "minutes" in text_lower or "discussed" in text_lower:
        return "Meeting Notes"
    if "customer" in text_lower and ("complaint" in text_lower or "refund" in text_lower or "dissatisfied" in text_lower):
        return "Customer Complaint"
    if "maintenance" in text_lower and ("report" in text_lower or "inspect" in text_lower or "unit" in text_lower):
        return "Maintenance Report"
    if "incident" in text_lower or "outage" in text_lower or "production stopped" in text_lower:
        return "Incident Report"
    if "ticket" in text_lower or "complaint" in text_lower or "issue" in text_lower or "fault" in text_lower:
        return "Support Ticket"
    if "project" in text_lower and ("update" in text_lower or "milestone" in text_lower or "timeline" in text_lower):
        return "Project Update"
    if "subject:" in text_lower or "from:" in text_lower or "email" in text_lower:
        return "Email"
    if "invoice" in text_lower or "purchase order" in text_lower or "supplier" in text_lower:
        return "Procurement Document"
    if "request" in text_lower or "please" in text_lower:
        return "Task Request"
    if "report" in text_lower:
        return "Report"

    return "General Document"


def detect_priority(text):
    text_lower = text.lower()

    high_words = [
        "urgent", "immediately", "critical", "asap", "high priority",
        "failure", "outage", "production stopped", "blocked", "safety"
    ]
    medium_words = [
        "soon", "important", "by tomorrow", "by friday", "by monday",
        "by tuesday", "by wednesday", "by thursday", "this week",
        "delay", "delays", "confusion", "before the next"
    ]

    for word in high_words:
        if contains_keyword(text_lower, word):
            return "High"

    for word in medium_words:
        if contains_keyword(text_lower, word):
            return "Medium"

    return "Low"


def detect_urgency(text):
    text_lower = text.lower()

    urgent_words = ["urgent", "immediately", "asap", "by tomorrow", "critical", "before the next"]
    moderate_words = [
        "soon", "this week", "next week", "important", "by friday",
        "by monday", "by tuesday", "by wednesday", "by thursday"
    ]

    for word in urgent_words:
        if contains_keyword(text_lower, word):
            return "Urgent"

    for word in moderate_words:
        if contains_keyword(text_lower, word):
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


def extract_email_metadata(text):
    metadata = {
        "from": "",
        "to": "",
        "subject": "",
    }
    for line in text.splitlines()[:20]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if key in metadata:
            metadata[key] = value.strip()
    return metadata


def assess_business_impact(result):
    if result.get("category") in {"Job Application Rejection", "Personal Message"}:
        return "Low impact: no operational action required."
    if result.get("category") in {"Job Alert / Career Opportunity", "Event / Ticket Alert", "Marketing / Promotion"}:
        return "Medium impact: review only if it matches current priorities."
    if result.get("priority") == "High" or result.get("urgency") == "Urgent":
        return "High impact: immediate review recommended."
    if result.get("risks") or result.get("deadlines"):
        return "Medium impact: follow-up should be planned and tracked."
    return "Low impact: document can be handled through the normal workflow."


def suggest_workflow_status(result):
    category = result.get("category")
    if category == "Job Application Rejection":
        return "Track outcome"
    if category in {"Job Alert / Career Opportunity", "Marketing / Promotion", "Event / Ticket Alert", "Interview Invitation", "Job Application Update"}:
        return "Ready for review"
    if category in {"Personal Message", "Schedule / Timetable", "Reminder"}:
        return "Informational"
    if result.get("human_review", {}).get("review_required"):
        return "Needs human review"
    if result.get("action_items"):
        return "Ready for task routing"
    return "Needs clarification"


def build_recommended_action(result):
    action_items = result.get("action_items", [])
    responsible_team = result.get("responsible_team", "Not clearly identified")
    involved_teams = result.get("involved_teams", [])
    deadlines = result.get("deadlines", [])
    priority = result.get("priority", "Low")
    category = result.get("category", "")

    if category == "Job Application Rejection":
        return "Archive the rejection, track the application outcome, and continue with suitable open roles."
    if category == "Job Alert / Career Opportunity":
        return "Review the role fit, save the job link, and decide whether to apply."
    if category == "Interview Invitation":
        return "Prioritize scheduling the interview and prepare the required documents."
    if category == "Job Application Update":
        return "Review the update and track the next hiring-process step."
    if category == "Event / Ticket Alert":
        return "Review availability, price, and date before deciding whether to book."
    if category == "Reminder":
        return "Add the reminder to the calendar or mark it as completed."
    if category == "Schedule / Timetable":
        return "Review the timetable and add important items to the calendar."
    if category == "Marketing / Promotion":
        return "Review only if the offer is relevant; otherwise archive or unsubscribe."
    if category == "Personal Message":
        return "No business action required."

    if action_items:
        next_action = action_items[0]
    elif result.get("risks"):
        next_action = "Review the risk indicators and define a clear owner."
    else:
        next_action = "Review the document and confirm whether follow-up is required."

    deadline_text = f" Deadline: {deadlines[0]}." if deadlines else ""
    support_teams = [team for team in involved_teams if team != responsible_team]
    support_text = f" Coordinate with {', '.join(support_teams[:2])}." if support_teams else ""
    return f"Route to {responsible_team}. Priority: {priority}.{support_text} Next action: {next_action}{deadline_text}"


def validate_structured_output(result):
    category = result.get("category")
    action_optional_categories = {
        "Job Application Rejection",
        "Job Application Update",
        "Interview Invitation",
        "Marketing / Promotion",
        "Personal Message",
        "Job Alert / Career Opportunity",
        "Event / Ticket Alert",
        "Reminder",
        "Schedule / Timetable",
    }
    checks = {
        "summary_present": bool(result.get("summary")),
        "category_present": bool(result.get("category")),
        "priority_present": bool(result.get("priority")),
        "urgency_present": bool(result.get("urgency")),
        "responsible_team_present": result.get("responsible_team") != "Not clearly identified",
        "action_items_present": bool(result.get("action_items")) or category in action_optional_categories,
        "keywords_present": bool(result.get("keywords")),
    }
    score = round(sum(checks.values()) / len(checks) * 100)
    missing_fields = [field for field, passed in checks.items() if not passed]
    return {
        "validation_score": score,
        "checks": checks,
        "missing_fields": missing_fields,
    }


def build_human_review_flag(result):
    reasons = []
    category = result.get("category")
    action_optional_categories = {
        "Job Application Rejection",
        "Job Application Update",
        "Interview Invitation",
        "Marketing / Promotion",
        "Personal Message",
        "Job Alert / Career Opportunity",
        "Event / Ticket Alert",
        "Reminder",
        "Schedule / Timetable",
    }
    if result.get("priority") == "High":
        reasons.append("High priority document")
    if result.get("urgency") == "Urgent":
        reasons.append("Urgent timeline detected")
    if result.get("risks"):
        reasons.append("Risk indicators detected")
    if not result.get("action_items") and category not in action_optional_categories:
        reasons.append("No clear action item extracted")
    if result.get("responsible_team") == "Not clearly identified":
        reasons.append("Responsible team unclear")

    return {
        "review_required": bool(reasons),
        "reasons": reasons,
    }


def build_result(text, summary):
    result = {
        "summary": summary,
        "email_metadata": extract_email_metadata(text),
        "action_items": extract_action_items(text),
        "category": detect_category(text),
        "priority": detect_priority(text),
        "urgency": detect_urgency(text),
        "responsible_team": detect_responsible_team(text),
        "involved_teams": detect_involved_teams(text),
        "deadlines": extract_deadlines(text),
        "risks": extract_risk_indicators(text),
        "sentiment": detect_sentiment(text),
        "keywords": extract_keywords(text),
    }
    result["recommended_next_action"] = build_recommended_action(result)
    result["validation"] = validate_structured_output(result)
    result["human_review"] = build_human_review_flag(result)
    result["business_impact"] = assess_business_impact(result)
    result["workflow_status"] = suggest_workflow_status(result)
    return result
