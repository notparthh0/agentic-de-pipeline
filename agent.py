import os
import sys

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

from tools.bq_tools import run_bq_query, get_table_stats, get_category_breakdown
from tools.anomaly_tools import detect_anomalies
from tools.report_tools import generate_report


@tool
def query_pipeline_data(sql: str) -> str:
    """Run a SQL query on the BigQuery fact_orders table and return results."""
    return run_bq_query(sql)


@tool
def scan_pipeline_health() -> str:
    """Scan the pipeline for data quality issues. Use this first."""
    report = detect_anomalies()
    lines = [
        f"Total rows: {report['total_rows']:,}",
        f"Health score: {report['health_score']}%",
        f"Avg transaction: ${report['avg_amount']}",
        f"Issues found: {report['issues_found']}",
        "",
        "Issues:",
    ]
    for issue in report["issues"]:
        lines.append(f"  [{issue['severity']}] {issue['type']}: {issue['description']}")
    if not report["issues"]:
        lines.append("  None found.")
    return "\n".join(lines)


@tool
def get_category_stats() -> str:
    """Get per-category row counts, avg amounts, and null counts."""
    cats = get_category_breakdown()
    lines = ["Category breakdown:"]
    for c in cats:
        lines.append(f"  {c['category']}: {c['row_count']} rows | avg=${c['avg_amount']} | nulls={c['null_count']}")
    return "\n".join(lines)


@tool
def generate_incident_report(analysis: str, recommendations: str) -> str:
    """Generate an HTML incident report. Call this last with your findings."""
    anomaly_report = detect_anomalies()
    category_data = get_category_breakdown()
    filepath = generate_report(anomaly_report, analysis, recommendations, category_data)
    return f"Report saved: {filepath}"


SYSTEM_PROMPT = """You are a data pipeline monitor. When asked to check a pipeline:
1. Start with scan_pipeline_health to get an overview
2. Use get_category_stats to break down issues by category
3. Use query_pipeline_data for any specific SQL you need
4. Finish with generate_incident_report — include specific numbers in your analysis

Be direct. Reference actual values from the data. Don't pad your response."""


def run_agent(task: str):
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    llm = ChatOllama(model=model, temperature=0)

    tools = [query_pipeline_data, scan_pipeline_health, get_category_stats, generate_incident_report]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)

    result = executor.invoke({"input": task})
    print(result["output"])
    return result["output"]


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Check the ecommerce pipeline for data quality issues and generate an incident report."
    )
    run_agent(task)
