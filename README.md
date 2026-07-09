# Autonomous Data Pipeline Monitor Agent

> **Python · LangChain · Llama3.2 · BigQuery · GCP**

An AI agent that autonomously monitors live BigQuery data pipelines, detects anomalies, reasons about root causes like a senior Data Reliability Engineer, and generates professional HTML incident reports — **with zero human intervention.**

---

## Architecture

```
Natural Language Task
        │
        ▼
┌─────────────────────────────────────────┐
│         LangChain Agent (ReAct)         │
│         Powered by Llama3.2:3b          │
└────────────┬────────────────────────────┘
             │ decides which tools to call
     ┌───────┴────────┬────────────────┐
     ▼                ▼                ▼
scan_pipeline    query_pipeline   get_category
   _health()       _data(sql)       _stats()
     │                │                │
     └───────┬─────────┘────────────────┘
             ▼
    generate_incident_report()
             │
             ▼
    📄 HTML Incident Report
```

---

## What It Does

| Step | Action | Technology |
|------|--------|-----------|
| 1 | Scans 100K+ row BigQuery table for issues | google-cloud-bigquery |
| 2 | Detects nulls, outliers, row imbalances statistically | Python statistics module |
| 3 | Reasons about root cause using LLM | LangChain + Llama3.2 (local) |
| 4 | Queries specific SQL for deeper investigation | BigQuery DirectQuery |
| 5 | Generates full HTML incident report | Jinja2 |

---

## Resume Bullets Demonstrated

| Claim | Where Implemented |
|-------|-----------------|
| Modular autonomous AI pipeline using LangChain and LLM APIs | `agent.py` — LangChain tool-calling agent |
| Executing structured DE workflows from natural language | `run_agent(task)` — any plain English task |
| Multi-step LLM reasoning pipelines | AgentExecutor with 4 chained tools |
| Automated tool-use on real-world DE contexts | Live BigQuery `fact_orders` table (100K rows) |

---

## Project Structure

```
agentic-de-pipeline/
├── agent.py                  # Main LangChain agent
├── tools/
│   ├── bq_tools.py           # BigQuery query & stats tools
│   ├── anomaly_tools.py      # Statistical anomaly detection
│   └── report_tools.py       # HTML incident report generator
├── reports/                  # Generated HTML reports
├── .env.example              # Environment variables template
└── requirements.txt
```

---

## Setup

```bash
# 1. Install Ollama (https://ollama.com) and pull the model
ollama pull llama3.2:3b

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Add your GCP credentials path and project ID

# 4. Run the agent
python agent.py "Monitor the pipeline and find any data quality issues"
```

---

## Example Output

```
🤖 AGENT TASK: Monitor the ecommerce data pipeline

> Invoking: scan_pipeline_health
  Total rows: 100,000 | Health: 85% | Issues: 1
  [MEDIUM] NULL_VALUES: 2039 null values (2.04%) in 'amount'

> Invoking: get_category_stats
  Clothing: 19988 rows | avg=$231.79 | nulls=430
  Electronics: 20172 rows | avg=$232.24 | nulls=426
  ...

> Invoking: generate_incident_report
  ✅ Report saved: reports/incident_report_2026-07-09.html
```

---

## Switching to Gemini API

To use Google Gemini instead of local Ollama, change one line in `agent.py`:

```python
# From:
llm = ChatOllama(model="llama3.2:3b", temperature=0)

# To:
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="YOUR_KEY")
```
