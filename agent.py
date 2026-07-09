"""
Autonomous Data Pipeline Monitor Agent
Uses LangChain + Llama3.2 (local) to monitor BigQuery pipelines,
detect anomalies, reason about root causes, and generate incident reports.
"""
import sys
import warnings
warnings.filterwarnings("ignore")

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

from tools.bq_tools import run_bq_query, get_table_stats, get_category_breakdown
from tools.anomaly_tools import detect_anomalies
from tools.report_tools import generate_report

# ── LangChain Tools ─────────────────────────────────────────────────────────

@tool
def query_pipeline_data(sql: str) -> str:
    """
    Run a SQL query on the live BigQuery ecommerce pipeline table (fact_orders).
    The table has columns: event_id, timestamp, user_id, event_type, product_id,
    category, amount, country, device, session_id, date_key, is_weekend.
    Always use backtick table name: `gen-lang-client-0938212760.ecommerce_analytics.fact_orders`
    """
    return run_bq_query(sql)


@tool
def scan_pipeline_health() -> str:
    """
    Run a full automated health scan on the BigQuery pipeline.
    Returns table stats, null counts, and any anomalies detected.
    Use this as the first step when asked to monitor or audit the pipeline.
    """
    report = detect_anomalies()
    lines = [
        f"PIPELINE HEALTH SCAN RESULTS",
        f"Total rows: {report['total_rows']:,}",
        f"Health score: {report['health_score']}%",
        f"Avg transaction: ${report['avg_amount']}",
        f"Issues found: {report['issues_found']}",
        "",
        "ISSUES:",
    ]
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"  [{issue['severity']}] {issue['type']}: {issue['description']}")
    else:
        lines.append("  None — pipeline is healthy!")
    return "\n".join(lines)


@tool
def get_category_stats() -> str:
    """
    Get per-category breakdown of the pipeline data.
    Returns row counts, average amounts, null counts per category.
    Use this to identify which categories have problems.
    """
    cats = get_category_breakdown()
    lines = ["CATEGORY BREAKDOWN:"]
    for c in cats:
        lines.append(
            f"  {c['category']}: {c['row_count']} rows | avg=${c['avg_amount']} | nulls={c['null_count']}"
        )
    return "\n".join(lines)


@tool
def generate_incident_report(analysis: str, recommendations: str) -> str:
    """
    Generate a professional HTML incident report with the agent's analysis and recommendations.
    Call this as the final step after completing the investigation.
    analysis: Your root cause analysis text
    recommendations: Your recommended actions text
    """
    anomaly_report = detect_anomalies()
    category_data = get_category_breakdown()
    filepath = generate_report(anomaly_report, analysis, recommendations, category_data)
    return f"✅ Incident report generated: {filepath}"


# ── Agent Setup ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an Autonomous Data Pipeline Monitor Agent specializing in Data Engineering.
Your job is to:
1. Monitor live BigQuery data pipelines for issues
2. Detect anomalies, null values, statistical outliers, and data quality problems
3. Reason about root causes like a senior Data Engineer would
4. Generate professional incident reports

When asked to monitor or audit a pipeline:
- ALWAYS start with scan_pipeline_health to get an overview
- Use query_pipeline_data for specific SQL investigations
- Use get_category_stats to understand per-category issues
- End with generate_incident_report containing your full analysis

Be specific and technical in your analysis. Reference actual numbers from the data.
Think step by step like a senior Data Reliability Engineer."""


def run_agent(task: str):
    """Run the agent with a given task."""
    print(f"\n{'='*60}")
    print(f"🤖 AGENT TASK: {task}")
    print(f"{'='*60}\n")

    llm = ChatOllama(model="llama3.2:3b", temperature=0)

    tools = [query_pipeline_data, scan_pipeline_health, get_category_stats, generate_incident_report]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)

    result = executor.invoke({"input": task})
    print(f"\n{'='*60}")
    print(f"✅ AGENT FINAL RESPONSE:")
    print(f"{'='*60}")
    print(result["output"])
    return result["output"]


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Monitor the ecommerce data pipeline. Scan for any data quality issues, "
        "investigate the root cause, and generate a full incident report."
    )
    run_agent(task)
