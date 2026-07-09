"""BigQuery tools — query the live ecommerce pipeline data."""
import os
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "gen-lang-client-0938212760"
TABLE = "gen-lang-client-0938212760.ecommerce_analytics.fact_orders"
CREDS_PATH = "/Users/parthalagh/claude/gcp-data-pipeline/service-account-key.json"


def get_bq_client():
    creds = service_account.Credentials.from_service_account_file(CREDS_PATH)
    return bigquery.Client(credentials=creds, project=PROJECT_ID)


def run_bq_query(sql: str) -> str:
    """Run a SQL query on the BigQuery ecommerce table and return results as string."""
    try:
        client = get_bq_client()
        rows = list(client.query(sql).result())
        if not rows:
            return "Query returned 0 rows."
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        lines.append("-" * 60)
        for row in rows[:20]:  # cap at 20 rows for agent context
            lines.append(" | ".join(str(v) for v in row.values()))
        if len(rows) > 20:
            lines.append(f"... ({len(rows)} total rows, showing 20)")
        return "\n".join(lines)
    except Exception as e:
        return f"BigQuery error: {e}"


def get_table_stats() -> dict:
    """Return key stats about the fact_orders table."""
    client = get_bq_client()
    sql = """
    SELECT
      COUNT(*) as total_rows,
      COUNTIF(amount IS NULL) as null_amounts,
      COUNTIF(country IS NULL) as null_countries,
      COUNTIF(category IS NULL) as null_categories,
      COUNTIF(user_id IS NULL) as null_users,
      ROUND(AVG(amount), 2) as avg_amount,
      ROUND(MIN(amount), 2) as min_amount,
      ROUND(MAX(amount), 2) as max_amount,
      COUNT(DISTINCT category) as distinct_categories,
      COUNT(DISTINCT country) as distinct_countries,
      ROUND(COUNTIF(amount IS NULL) / COUNT(*) * 100, 2) as null_pct
    FROM `gen-lang-client-0938212760.ecommerce_analytics.fact_orders`
    """
    rows = list(client.query(sql).result())
    return dict(rows[0]) if rows else {}


def get_category_breakdown() -> list:
    """Return per-category stats to detect anomalies."""
    client = get_bq_client()
    sql = """
    SELECT
      category,
      COUNT(*) as row_count,
      COUNTIF(amount IS NULL) as null_count,
      ROUND(AVG(amount), 2) as avg_amount,
      ROUND(STDDEV(amount), 2) as stddev_amount,
      ROUND(MIN(amount), 2) as min_amount,
      ROUND(MAX(amount), 2) as max_amount
    FROM `gen-lang-client-0938212760.ecommerce_analytics.fact_orders`
    GROUP BY category
    ORDER BY null_count DESC
    """
    return [dict(r) for r in client.query(sql).result()]
