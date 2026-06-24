"""Ranking stability summaries."""

from __future__ import annotations

from pathlib import Path

from certgen.core.io import read_json, write_json


def build_ranking_stability(batch_json: str | Path, out: str | Path, json_out: str | Path) -> dict:
    rows = read_json(batch_json).get("rows", [])
    edges = []
    undecided = []
    for row in rows:
        cid = row.get("comparison_id", "")
        if row.get("decision") == "A_better":
            edges.append({"comparison_id": cid, "edge": "A>B"})
        elif row.get("decision") == "B_better":
            edges.append({"comparison_id": cid, "edge": "B>A"})
        else:
            undecided.append(cid)
    payload = {"naive_ranking": [], "certified_partial_order": edges, "undecided_edges": undecided, "claim_allowed": False, "evidence_status": "synthetic_only"}
    write_json(payload, json_out)
    lines = ["# V4 Ranking Stability", "", "`NON-EVIDENCE / TEMPLATE / SYNTHETIC`", "", f"- Certified edges: `{len(edges)}`", f"- Undecided edges: `{len(undecided)}`"]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload
