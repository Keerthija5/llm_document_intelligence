# LLM-Based Business Document Triage Dashboard

This project is a practical document intelligence system for converting unstructured business text into structured workflow-ready outputs. It compares BART and T5 summaries, classifies incoming documents or emails, extracts action items and business fields, flags documents that need human review, and exports results as JSON or CSV.

I built this project to understand how LLM-based summarisation and rule-based evaluation can be combined in a useful workflow. Instead of only generating a summary, the system tries to answer practical questions such as:

- What type of document is this?
- Is it urgent or high priority?
- Which team or workflow should handle it?
- Are there risks, deadlines, or action items?
- Which model output is more useful?
- Does the extracted output need human review?

## Features

- Streamlit dashboard for processing pasted text or uploaded `.txt`, `.md`, and `.eml` files
- BART and T5 summarisation using Hugging Face Transformers
- Model comparison using summary quality, keyword coverage, action-item coverage, repetition, and length checks
- Classification of business and everyday communication types
- Structured extraction of priority, urgency, responsible team, involved teams, risks, deadlines, sentiment, and recommended next action
- Human-review flag for urgent, risky, unclear, or operationally important documents
- Output validation score for checking whether required structured fields are present
- Batch triage table for reviewing multiple documents
- JSON and CSV export for downstream analysis or reporting

## Supported Document Types

The system handles several practical text categories:

- Maintenance reports
- Support tickets
- Customer complaints
- Meeting notes
- Project updates
- Incident reports
- Procurement documents
- Job alerts and career updates
- Job rejection emails
- Interview invitations
- Reminders and schedules
- Marketing or event alerts
- Personal messages

## Screenshots

### Upload and Paste Interface
![Upload and Paste Interface](assets/screenshots/upload-page.png)

### Batch Triage Table
![Batch Triage Table](assets/screenshots/batch-triage-table.png)

### Structured Extraction
![Structured Extraction](assets/screenshots/structured-extraction.png)

### Model Evaluation and Validation
![Model Evaluation and Validation](assets/screenshots/model-evaluation-validation.png)

## Example Workflow

```text
Input document or email
        |
BART and T5 summarisation
        |
Business category detection
        |
Priority, urgency, risks, deadlines, and team extraction
        |
Model output evaluation
        |
Human-review and validation checks
        |
JSON / CSV export
```

## Example Use Case

Input:

```text
The maintenance team reported repeated faults in the conveyor sensor system during the evening shift. Engineering should review the fault logs and identify the possible root cause. Maintenance needs to inspect the unit before the next production cycle. A short update should be shared with the operations manager by tomorrow morning.
```

Expected structured output:

```json
{
  "category": "Maintenance Report",
  "priority": "Medium",
  "urgency": "Urgent",
  "responsible_team": "Maintenance",
  "involved_teams": ["Maintenance", "Engineering", "Operations", "Management"],
  "risks": ["fault", "root cause"],
  "deadlines": ["by tomorrow morning", "before the next production cycle"],
  "workflow_status": "Needs human review",
  "business_impact": "High impact: immediate review recommended."
}
```

## Tech Stack

- Python
- Streamlit
- Hugging Face Transformers
- BART (`facebook/bart-large-cnn`)
- T5 (`t5-small`)
- Pandas
- Rule-based NLP and validation logic

## Project Structure

```text
app.py
requirements.txt
src/
  main.py
  llm_processor.py
  parser.py
  evaluator.py
  exporter.py
  file_handler.py
data/
  input/
  output/
assets/
  screenshots/
```

## How to Run

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit dashboard:

```bash
python3 -m streamlit run app.py
```

The first processing run can take longer because BART and T5 load locally. Short alerts and very small texts are handled without forcing long model summaries.

## Command-Line Batch Processing

The project also supports batch processing from the command line:

```bash
python3 src/main.py
```

Input files are read from:

```text
data/input/
```

Outputs are written to:

```text
data/output/
```

## What I Learned

This project helped me understand that document intelligence is not only about generating summaries. A useful system also needs structured extraction, output validation, model comparison, and human-review logic. I also learned that classification rules need to be tested with real examples, because short messages, job alerts, rejection emails, and operational reports behave differently.

## Current Limitations

- The summarisation models run locally and can be slow on a laptop.
- The classification and routing logic is rule-based, so it can be improved with trained classifiers in the future.
- Screenshot/image OCR is not included in this version.
- PDF support is not the focus of this project; this system is mainly for text, email, and business communication triage.

## Future Improvements

- Add OCR support for screenshots and scanned documents
- Add PDF and DOCX parsing
- Add a trained classifier for category detection
- Add confidence scores for category and team routing
- Add a lightweight database for tracking document history
- Add charts for category distribution and review workload

## Resume Summary

Built a Streamlit-based LLM document triage dashboard that compares BART and T5 summaries, classifies unstructured business documents and emails, extracts workflow fields such as category, priority, urgency, responsible team, risks, deadlines, action items, and recommended next action, and exports validated JSON/CSV outputs with human-review flags.
