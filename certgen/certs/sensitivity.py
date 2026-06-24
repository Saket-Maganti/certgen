"""V4 certificate sensitivity summaries."""

from __future__ import annotations


def summarize_sensitivity(rows: list[dict]) -> dict:
    by_comparison: dict[str, dict] = {}
    for row in rows:
        cid = row.get("comparison_id")
        entry = by_comparison.setdefault(cid, {"decisions": set(), "metrics": set(), "budgets": set(), "seeds": set()})
        entry["decisions"].add(row.get("decision"))
        entry["metrics"].add(row.get("metric_name"))
        entry["budgets"].add(row.get("n_max"))
        entry["seeds"].add(row.get("seed"))
    return {
        cid: {
            "decision_count": len(v["decisions"]),
            "metric_count": len(v["metrics"]),
            "budget_count": len(v["budgets"]),
            "seed_count": len(v["seeds"]),
            "decisions": sorted(str(x) for x in v["decisions"]),
        }
        for cid, v in by_comparison.items()
    }
