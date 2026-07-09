"""Anomaly detection tools — finds data quality issues in the pipeline."""
import statistics
from tools.bq_tools import get_table_stats, get_category_breakdown


def detect_anomalies() -> dict:
    """
    Run automated anomaly detection on the live BigQuery table.
    Returns a structured report of all issues found.
    """
    issues = []
    stats = get_table_stats()
    categories = get_category_breakdown()

    # 1. Null value check
    for col in ["null_amounts", "null_countries", "null_categories", "null_users"]:
        if stats.get(col, 0) > 0:
            pct = round(stats[col] / stats["total_rows"] * 100, 2)
            issues.append({
                "type": "NULL_VALUES",
                "severity": "HIGH" if pct > 5 else "MEDIUM",
                "column": col.replace("null_", ""),
                "count": stats[col],
                "percentage": pct,
                "description": f"{stats[col]} null values ({pct}%) in column '{col.replace('null_', '')}'"
            })

    # 2. Category row count imbalance
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
                    "column": "category",
                    "category": cat["category"],
                    "count": cat["row_count"],
                    "expected": round(mean_count),
                    "z_score": round(z_score, 2),
                    "description": f"Category '{cat['category']}' has {cat['row_count']} rows (z-score: {round(z_score,2)}), significantly different from mean {round(mean_count)}"
                })

    # 3. Amount outlier detection
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
                            "column": "amount",
                            "category": cat["category"],
                            "avg_amount": cat["avg_amount"],
                            "global_mean": round(global_mean, 2),
                            "z_score": round(z, 2),
                            "description": f"Category '{cat['category']}' avg amount ${cat['avg_amount']} is a statistical outlier (z={round(z,2)})"
                        })

    return {
        "total_rows": stats.get("total_rows", 0),
        "null_percentage": stats.get("null_pct", 0),
        "avg_amount": stats.get("avg_amount", 0),
        "issues_found": len(issues),
        "issues": issues,
        "health_score": max(0, 100 - (len(issues) * 15))
    }
