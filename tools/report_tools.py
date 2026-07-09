import os
from datetime import datetime
from jinja2 import Environment

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pipeline Incident Report — {{ date }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e2e8f0; padding: 2rem; }
  h1 { font-size: 1.8rem; color: #7c3aed; margin-bottom: 0.5rem; }
  .subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }
  .card { background: #1e2130; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border-left: 4px solid #7c3aed; }
  .card h2 { font-size: 1.1rem; color: #a78bfa; margin-bottom: 1rem; }
  .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
  .metric { background: #1e2130; border-radius: 10px; padding: 1.2rem; text-align: center; }
  .metric .value { font-size: 2rem; font-weight: bold; color: #7c3aed; }
  .metric .label { font-size: 0.8rem; color: #94a3b8; margin-top: 0.3rem; }
  .issue { background: #252840; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; border-left: 3px solid #ef4444; }
  .issue.medium { border-left-color: #f59e0b; }
  .issue.low { border-left-color: #10b981; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
  .badge.HIGH { background: #7f1d1d; color: #fca5a5; }
  .badge.MEDIUM { background: #78350f; color: #fde68a; }
  .analysis { background: #1a2744; border-radius: 8px; padding: 1.2rem; line-height: 1.7; white-space: pre-wrap; font-size: 0.9rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { background: #252840; padding: 0.6rem 1rem; text-align: left; color: #a78bfa; }
  td { padding: 0.6rem 1rem; border-bottom: 1px solid #252840; }
  tr:hover td { background: #252840; }
</style>
</head>
<body>
<h1>Pipeline Incident Report</h1>
<p class="subtitle">Generated: {{ date }} | Table: {{ table }}</p>

<div class="metrics">
  <div class="metric">
    <div class="value">{{ total_rows | format_num }}</div>
    <div class="label">Total Rows</div>
  </div>
  <div class="metric">
    <div class="value">{{ issues_found }}</div>
    <div class="label">Issues Found</div>
  </div>
  <div class="metric">
    <div class="value">${{ avg_amount }}</div>
    <div class="label">Avg Transaction</div>
  </div>
  <div class="metric">
    <div class="value" style="color: {% if health >= 80 %}#10b981{% elif health >= 50 %}#f59e0b{% else %}#ef4444{% endif %}">{{ health }}%</div>
    <div class="label">Pipeline Health</div>
  </div>
</div>

<div class="card">
  <h2>Issues Detected</h2>
  {% if issues %}
    {% for issue in issues %}
    <div class="issue {{ issue.severity.lower() if issue.severity != 'HIGH' else '' }}">
      <span class="badge {{ issue.severity }}">{{ issue.severity }}</span>
      <strong> {{ issue.type }}</strong> — {{ issue.description }}
    </div>
    {% endfor %}
  {% else %}
    <p style="color:#10b981">No anomalies detected.</p>
  {% endif %}
</div>

<div class="card">
  <h2>Root Cause Analysis</h2>
  <div class="analysis">{{ analysis }}</div>
</div>

<div class="card">
  <h2>Recommended Actions</h2>
  <div class="analysis">{{ recommendations }}</div>
</div>

<div class="card">
  <h2>Category Breakdown</h2>
  <table>
    <tr><th>Category</th><th>Rows</th><th>Avg Amount</th><th>Null Count</th></tr>
    {% for row in category_data %}
    <tr>
      <td>{{ row.category }}</td>
      <td>{{ row.row_count | int }}</td>
      <td>${{ row.avg_amount }}</td>
      <td>{{ row.null_count | int }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
</body>
</html>
"""


def generate_report(anomaly_report: dict, analysis: str, recommendations: str, category_data: list) -> str:
    """Generate an HTML incident report and save it to the reports/ directory."""
    def format_num(value):
        return f"{int(value):,}"

    env = Environment()
    env.filters["format_num"] = format_num
    template = env.from_string(TEMPLATE)

    health = anomaly_report.get("health_score", 100)
    table_name = os.getenv("BQ_TABLE", "ecommerce_analytics.fact_orders")
    html = template.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_rows=anomaly_report.get("total_rows", 0),
        issues_found=anomaly_report.get("issues_found", 0),
        avg_amount=anomaly_report.get("avg_amount", 0),
        health=health,
        issues=anomaly_report.get("issues", []),
        analysis=analysis,
        recommendations=recommendations,
        category_data=category_data,
        table=table_name,
    )

    os.makedirs("reports", exist_ok=True)
    filename = f"reports/incident_report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.html"
    with open(filename, "w") as f:
        f.write(html)
    return filename
