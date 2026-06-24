"""Claim trace construction."""

from __future__ import annotations


def build_claim_trace(row: dict, provenance_row: str = "", feature_cache_ids: list[str] | None = None, certificate_ids: list[str] | None = None) -> dict:
    return {
        "claim_id": row.get("claim_id"),
        "source": row.get("paper_title"),
        "reported_values": {"a": row.get("reported_score_a"), "b": row.get("reported_score_b"), "direction": row.get("reported_direction")},
        "availability": {
            "released_samples_available": row.get("released_samples_available"),
            "checkpoint_available": row.get("checkpoint_available"),
            "feature_stats_available": row.get("feature_stats_available"),
        },
        "provenance_row": provenance_row,
        "feature_cache_ids": feature_cache_ids or [],
        "preprocessing_lock_id": row.get("reported_preprocessing"),
        "metric_reproduction_id": row.get("reproduction_status"),
        "certificate_ids": certificate_ids or [],
        "decidedness_status": row.get("certgen_status", "not_run"),
        "claim_allowed": False,
    }
