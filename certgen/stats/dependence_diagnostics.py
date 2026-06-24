"""Dependence diagnostics for reused models/caches/reference sets."""

from __future__ import annotations

from collections import Counter


def dependence_warnings(rows: list[dict]) -> dict[str, list[str]]:
    warnings: dict[str, list[str]] = {}
    refs = Counter(row.get("reference_cache") or row.get("reference_cache_id") or row.get("shared_reference_id") for row in rows)
    models = Counter()
    caches = Counter()
    for row in rows:
        for field in ["model_a", "model_b", "model_a_id", "model_b_id"]:
            if row.get(field):
                models[row[field]] += 1
        for field in ["features_a", "features_b", "features_r", "model_a_cache_id", "model_b_cache_id", "reference_cache_id"]:
            if row.get(field):
                caches[row[field]] += 1
    for row in rows:
        cid = row.get("comparison_id", "comparison")
        items = []
        ref = row.get("reference_cache") or row.get("reference_cache_id") or row.get("shared_reference_id")
        if ref and refs[ref] > 1:
            items.append("overlapping reference samples/cache reused")
        for field in ["model_a", "model_b", "model_a_id", "model_b_id"]:
            if row.get(field) and models[row[field]] > 1:
                items.append(f"model reused across comparisons: {row[field]}")
        for field in ["features_a", "features_b", "features_r", "model_a_cache_id", "model_b_cache_id", "reference_cache_id"]:
            if row.get(field) and caches[row[field]] > 1:
                items.append(f"feature cache reused: {row[field]}")
        warnings[cid] = sorted(set(items))
    return warnings
