import os
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable is required")
TABLE = os.getenv("BQ_TABLE", f"{PROJECT_ID}.ecommerce_analytics.fact_orders")


def get_bq_client():
    # Uses GOOGLE_APPLICATION_CREDENTIALS env var automatically
    return bigquery.Client(project=PROJECT_ID)


def run_bq_query(sql: str) -> str:
    """Run a SQL query and return results as a formatted string."""
    try:
        client = get_bq_client()
        rows = list(client.query(sql).result())
        if not rows:
            return "Query returned 0 rows."
        headers = list(rows[0].keys())
        lines = [" | ".join(headers), "-" * 60]
        for row in rows[:20]:
            lines.append(" | ".join(str(v) for v in row.values()))
        if len(rows) > 20:
            lines.append(f"... {len(rows)} total rows, showing first 20")
        return "\n".join(lines)
    except BadRequest as e:
        return f"SQL error: {e}"
    except Exception as e:
        return f"BigQuery error: {e}"


def get_table_stats() -> dict:
    """Return summary stats for the fact_orders table."""
    client = get_bq_client()
    sql = f"""
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
    FROM `{TABLE}`
    """
    rows = list(client.query(sql).result())
    return dict(rows[0]) if rows else {}


def get_category_breakdown() -> list:
    """Return per-category stats."""
    client = get_bq_client()
    sql = f"""
    SELECT
      category,
      COUNT(*) as row_count,
      COUNTIF(amount IS NULL) as null_count,
      ROUND(AVG(amount), 2) as avg_amount,
      ROUND(STDDEV(amount), 2) as stddev_amount,
      ROUND(MIN(amount), 2) as min_amount,
      ROUND(MAX(amount), 2) as max_amount
    FROM `{TABLE}`
    GROUP BY category
    ORDER BY null_count DESC
    """
    return [dict(r) for r in client.query(sql).result()]
