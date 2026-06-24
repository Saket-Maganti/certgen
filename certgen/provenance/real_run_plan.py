"""Build non-claim real-run plans from provenance rows."""

from __future__ import annotations

from pathlib import Path

from certgen.core.io import write_json
from certgen.provenance.ledger import read_v4_ledger


CLEAN_METRICS = {"mmd", "mmd_rbf", "cmmd", "cmmd_clip_mmd"}
DESCRIPTIVE_METRICS = {"kid", "kid_polynomial", "fid", "fid_inception", "fd_dinov2"}


def build_real_run_plan(ledger: str | Path, comparison_id: str, out: str | Path, report: str | Path, requested_budget: int | None = None) -> dict:
    rows = [row for row in read_v4_ledger(ledger) if row.get("comparison_id") == comparison_id]
    blockers: list[str] = []
    warnings: list[str] = []
    if not rows:
        blockers.append(f"comparison_id not found: {comparison_id}")
        row = {}
    else:
        row = rows[0]
    if row:
        if row.get("provenance_status") != "verified":
            blockers.append("provenance_status must be verified")
        if row.get("sample_license_status") not in {"verified_free", "allowed", "public_free"}:
            blockers.append("sample license not verified free/allowed")
        budget = requested_budget or int(float(row.get("reported_sample_size") or 0))
        for field in ["sample_count_available_a", "sample_count_available_b"]:
            try:
                if int(float(row.get(field, 0))) < budget:
                    blockers.append(f"{field} below requested budget")
            except ValueError:
                blockers.append(f"{field} not numeric")
        if row.get("reported_preprocessing") in {"", "unknown", "TBD"}:
            blockers.append("reported preprocessing is unknown")
        if not row.get("reference_set_source") or row.get("reference_set_source") == "TBD":
            blockers.append("reference set source missing")
        metric = row.get("reported_metric_name", "").lower()
        if metric not in CLEAN_METRICS and metric not in DESCRIPTIVE_METRICS:
            blockers.append(f"unsupported metric: {metric}")
        if row.get("claim_allowed", "false").lower() == "true":
            blockers.append("ledger row cannot set claim_allowed=true before results")
        if row.get("download_required") == "yes":
            warnings.append("download required; user must run manually")
    plan = {
        "run_id": f"real_run_plan_{comparison_id}",
        "comparison_id": comparison_id,
        "benchmark_id": row.get("benchmark_id"),
        "metrics": [row.get("reported_metric_name")] if row else [],
        "sample_budget": requested_budget or row.get("reported_sample_size"),
        "preprocessing_lock_id": row.get("reported_preprocessing"),
        "feature_cache_targets": {
            "reference": f"data/features/{comparison_id}/reference_features.npz",
            "model_a": f"data/features/{comparison_id}/model_a_features.npz",
            "model_b": f"data/features/{comparison_id}/model_b_features.npz",
        },
        "evidence_status": "real_verified_nonclaim" if not blockers else "planned_only",
        "claim_allowed": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_commands": [
            "python -m certgen.cli.generate_feature_notebook ...",
            "python -m certgen.cli.validate_feature_cache ...",
            "python -m certgen.cli.run_first_real_pilot ...",
        ],
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    write_json(plan, out)
    lines = ["# V4 Real Run Plan", "", "`NO_REAL_EVIDENCE`", "", f"Comparison: `{comparison_id}`", f"Evidence status: `{plan['evidence_status']}`", "Claim allowed: `False`", "", "## Blockers"]
    lines.extend(f"- {b}" for b in blockers or ["none"])
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return plan
