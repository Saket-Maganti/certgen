"""Decidedness audit classification."""

from __future__ import annotations

import csv
from pathlib import Path

from certgen.core.io import read_json, write_json


def classify_row(row: dict) -> str:
    if row.get("blocked_reason"):
        return row["blocked_reason"]
    if row.get("metric_name", "").startswith("fid"):
        return "descriptive_only"
    decision = row.get("decision")
    reported = row.get("reported_direction")
    if decision == "undecided":
        return "undecided_at_budget"
    if decision in {"A_better", "B_better"} and reported:
        return "decided_same_direction" if decision.startswith(reported[:1]) else "decided_opposite_direction"
    if decision in {"A_better", "B_better"}:
        return "decided_same_direction"
    return "blocked_provenance_missing"


def build_decidedness_audit(batch_json: str | Path, out_csv: str | Path, out_json: str | Path, report: str | Path) -> dict:
    rows = read_json(batch_json).get("rows", [])
    classified = [{**row, "decidedness_category": classify_row(row), "claim_allowed": False} for row in rows]
    counts: dict[str, int] = {}
    for row in classified:
        counts[row["decidedness_category"]] = counts.get(row["decidedness_category"], 0) + 1
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with Path(out_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted(classified[0].keys()) if classified else ["comparison_id"])
        writer.writeheader()
        writer.writerows(classified)
    payload = {"rows": classified, "counts": counts, "evidence_status": "synthetic_only", "claim_allowed": False}
    write_json(payload, out_json)
    lines = ["# V4 Decidedness Audit", "", "`NON-EVIDENCE / TEMPLATE / SYNTHETIC`", "", "| Category | Count |", "|---|---:|"]
    for key, value in sorted(counts.items()):
        lines.append(f"| `{key}` | {value} |")
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload
