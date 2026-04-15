# LLM-Based Document Intelligence System

## Overview

This project implements a document intelligence pipeline using Large Language Models (LLMs) to process unstructured business text and generate structured insights.

The system is designed to simulate real-world industrial use cases such as processing:

* maintenance reports
* support tickets
* meeting notes

It extracts meaningful information and converts raw text into structured outputs.

---

## Key Features

* Automated document processing pipeline
* LLM-based summarization using Hugging Face
* Model comparison (BART vs T5)
* Rule-based evaluation of model outputs
* Action item extraction
* Keyword extraction using NLP preprocessing
* Classification (category, priority, urgency)
* Structured outputs (JSON + CSV)

---

## Tech Stack

* Python
* Hugging Face Transformers
* Pandas
* Regular Expressions (NLP preprocessing)

---

## Project Structure

```
llm_document_intelligence/
│
├── src/
│   ├── main.py
│   ├── llm_processor.py
│   ├── parser.py
│   ├── evaluator.py
│   └── exporter.py
│
├── data/
│   └── input/
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## How It Works

1. Input text files are loaded from the data/input folder
2. Summaries are generated using two models:

   * BART (baseline)
   * T5 (comparison)
3. NLP techniques extract:

   * action items
   * keywords
   * document metadata
4. Evaluation logic compares model outputs
5. Results are stored in JSON and CSV format

---

## Model Comparison

### BART

* More fluent and structured output
* Better sentence formatting

### T5

* Generates longer summaries
* Slightly less structured formatting

The system evaluates both models based on:

* sentence completeness
* formatting quality
* length and readability
* repetition and structure

---

## Example Output

Each document produces:

* JSON file with structured information
* CSV file with combined results

Example fields:

* summary
* action_items
* category
* priority
* urgency
* keywords
* model comparison results

---

## How to Run

### Step 1: Create virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install dependencies

```
pip install -r requirements.txt
```

### Step 3: Run the project

```
python3 src/main.py
```

---

## Learning Outcomes

This project demonstrates:

* Application of LLMs in real-world workflows
* NLP preprocessing and feature extraction
* Model comparison and evaluation techniques
* Pipeline-based system design
* Structured data generation from unstructured inputs

---

## Future Improvements

* Advanced evaluation metrics (ROUGE, BLEU)
* TF-IDF or embedding-based keyword extraction
* Support for PDF/DOCX inputs
* Streamlit-based UI for visualization

---

## Author

Keerthija 
