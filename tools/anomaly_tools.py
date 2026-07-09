import statistics
from tools.bq_tools import get_table_stats, get_category_breakdown

SEVERITY_PENALTY = {"HIGH": 20, "MEDIUM": 10, "LOW": 5}


def detect_anomalies() -> dict:
    """Scan the BigQuery table for data quality issues."""
    issues = []
    stats = get_table_stats()
    categories = get_category_breakdown()

    # Null value check
    for col in ["null_amounts", "null_countries", "null_categories", "null_users"]:
        count = stats.get(col, 0)
        if count > 0:
            pct = round(count / stats["total_rows"] * 100, 2)
            field = col.replace("null_", "")
            issues.append({
                "type": "NULL_VALUES",
                "severity": "HIGH" if pct > 5 else "MEDIUM",
                "count": count,
                "percentage": pct,
                "description": f"{count} null values ({pct}%) in '{field}'"
            })

    # Row count imbalance across categories
    if categories:
        counts = [c["row_count"] for c in categories]
        mean_count = statistics.mean(counts)
        stdev_count = statistics.stdev(counts) if len(counts) > 1 else 0
        for cat in categories:
            z_score = abs(cat["row_count"] - mean_count) / stdev_count if stdev_count else 0
            if z_score > 2:
                issues.append({
                    "type": "ROW_IMBALANCE",
                    "severity": "MEDIUM",
                    "category": cat["category"],
                    "count": cat["row_count"],
                    "expected": round(mean_count),
                    "z_score": round(z_score, 2),
                    "description": f"'{cat['category']}' has {cat['row_count']} rows vs expected ~{round(mean_count)} (z={round(z_score,2)})"
                })

    # Amount outlier detection per category
    if categories:
        avg_amounts = [c["avg_amount"] for c in categories if c["avg_amount"]]
        if avg_amounts:
            global_mean = statistics.mean(avg_amounts)
            global_std = statistics.stdev(avg_amounts) if len(avg_amounts) > 1 else 0
            for cat in categories:
                if cat["avg_amount"] and global_std:
                    z = abs(cat["avg_amount"] - global_mean) / global_std
                    if z > 2:
                        issues.append({
                            "type": "AMOUNT_OUTLIER",
                            "severity": "HIGH",
                            "category": cat["category"],
                            "avg_amount": cat["avg_amount"],
                            "global_mean": round(global_mean, 2),
                            "z_score": round(z, 2),
                            "description": f"'{cat['category']}' avg amount ${cat['avg_amount']} is an outlier (z={round(z,2)}, global mean=${round(global_mean,2)})"
                        })

    penalty = sum(SEVERITY_PENALTY.get(i["severity"], 0) for i in issues)
    health_score = max(0, 100 - penalty)

    return {
        "total_rows": stats.get("total_rows", 0),
        "null_percentage": stats.get("null_pct", 0),
        "avg_amount": stats.get("avg_amount", 0),
        "issues_found": len(issues),
        "issues": issues,
        "health_score": health_score,
    }
