"""Samples-to-decision summaries."""

from __future__ import annotations


def samples_to_decision_from_states(states: list[dict]) -> int | None:
    """First CS step whose interval excludes zero, else None (undecided).

    Operates on the per-step ``states`` produced by any confidence sequence in
    :mod:`certgen.stats.cs`. This is the unit-level decision time; multiply by the
    block size to recover the raw-sample budget consumed.
    """

    for state in states:
        if state["upper"] < 0.0 or state["lower"] > 0.0:
            return int(state["n"])
    return None


def summarize_samples_to_decision(rows: list[dict], fixed_budget: int = 50000) -> list[dict]:
    out = []
    for row in rows:
        n = row.get("n_decision")
        if n:
            out.append({"comparison_id": row.get("comparison_id"), "samples_to_decision": n, "fraction_of_budget": n / max(1, row.get("n_max", n)), "fixed_budget_fraction": n / fixed_budget})
        else:
            width = None
            if row.get("cs_lower") is not None and row.get("cs_upper") is not None:
                width = row["cs_upper"] - row["cs_lower"]
            out.append({"comparison_id": row.get("comparison_id"), "budget_used": row.get("n_max"), "final_cs_width": width, "projected_sample_need": "heuristic_not_computed"})
    return out
