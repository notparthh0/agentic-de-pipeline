# agentic-de-pipeline

A LangChain agent that monitors a BigQuery data pipeline for quality issues and generates an HTML incident report.

I built this to get a feel for how LLM agents work in practice — specifically how tool-calling lets the model decide what to do next rather than you hard-coding a sequence of steps. The underlying data comes from the [gcp-data-pipeline](https://github.com/notparthh0/gcp-data-pipeline) project.

## What it does

You give the agent a task in plain English. It decides which tools to call, in what order, and generates a report at the end.

```
$ python agent.py "Check the pipeline for data quality issues and write a report"

> scan_pipeline_health()
  → 100,000 rows | health: 90% | 1 issue found
  → [MEDIUM] 2,039 null values (2.04%) in 'amount'

> get_category_stats()
  → Clothing: 19,988 rows | avg=$231.79 | nulls=430
  → Electronics: 20,172 rows | ...

> generate_incident_report(analysis, recommendations)
  → Report saved: reports/incident_report_2026-07-09.html
```

## Stack

- Python, LangChain, Ollama (llama3.2:3b running locally)
- Google BigQuery (live table from the GCP pipeline project)
- Jinja2 for the HTML report

## Setup

```bash
# Install Ollama and pull the model
ollama pull llama3.2:3b

pip install -r requirements.txt

cp .env.example .env
# Fill in your GCP project ID and credentials path

export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
python agent.py "Check the pipeline for issues"
```

## Project structure

```
agent.py              # Agent definition and tool wiring
tools/
  bq_tools.py         # BigQuery queries
  anomaly_tools.py    # Anomaly detection logic
  report_tools.py     # HTML report generation
reports/              # Generated reports go here
```

## Environment variables

| Variable | Description |
|---|---|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `BQ_TABLE` | Full table path (default: `{project}.ecommerce_analytics.fact_orders`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key |
| `OLLAMA_MODEL` | Ollama model to use (default: `llama3.2:3b`) |

## Notes

The anomaly detection is fairly basic — it checks for nulls, z-score outliers on row counts, and z-score outliers on average amounts per category. Z-score isn't always the right tool here (it assumes normality) but it works fine as a first pass with this dataset. Proper time-series comparison would be the next thing to add.

The health score is weighted: HIGH issues cost 20 points, MEDIUM cost 10, LOW cost 5. Starting at 100.

Swapping Ollama for the Gemini API is one line — change `ChatOllama` to `ChatGoogleGenerativeAI` in `agent.py`.
