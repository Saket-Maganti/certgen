"""Dry-run-safe first-pilot planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.registry.validate import read_csv, validate_model_pair_rows


def _row_ready(row: dict[str, str]) -> tuple[bool, list[str]]:
    missing = []
    if row.get("audit_eligibility") != "eligible":
        missing.append("audit_eligibility_not_eligible")
    if row.get("feature_cache_status") not in {"available", "ready"}:
        missing.append("feature_cache_missing")
    if row.get("license_status") not in {"verified", "public_free"}:
        missing.append("license_not_verified")
    if row.get("reported_preprocessing_note") in {"", "TBD", "unknown"}:
        missing.append("preprocessing_missing")
    return not missing, missing


def plan_first_pilot_v2(registry_dir: str | Path, out_json: str | Path, out_md: str | Path, *, dry_run: bool = True) -> dict[str, Any]:
    if not dry_run:
        raise ValueError("V2 first-pilot planner must be run with dry_run=True")
    registry_dir = Path(registry_dir)
    pair_path = registry_dir / "templates" / "candidate_model_pairs_template.csv"
    if not pair_path.exists():
        pair_path = registry_dir / "candidate_model_pairs_template.csv"
    rows = read_csv(pair_path)
    validation_errors = validate_model_pair_rows(rows)
    selected = None
    unavailable = []
    for row in rows:
        ready, reasons = _row_ready(row)
        if ready and selected is None:
            selected = row
        else:
            unavailable.append({"comparison_id": row.get("comparison_id") or row.get("pair_id"), "reasons": reasons or ["not_selected"]})
    plan = {
        "label": "NO_REAL_EVIDENCE",
        "evidence_status": "dry_run_only",
        "claim_status": "NO_REAL_CLAIMS_ALLOWED",
        "selected_benchmark": selected["benchmark_id"] if selected else "none_selected",
        "selected_model_pairs": [selected["comparison_id"]] if selected else [],
        "unavailable_pairs": unavailable,
        "validation_errors": validation_errors,
        "required_features": ["model_a_features", "model_b_features", "reference_features"],
        "missing_artifacts": [] if selected else ["verified registry row", "feature caches", "preprocessing policy"],
        "expected_clean_core_metrics": ["mmd_rbf", "cmmd_clip_mmd"],
        "descriptive_only_metrics": ["kid_polynomial", "fid_inception", "fd_dinov2"],
        "fid_descriptive_policy": "FID and FD-DINOv2 are descriptive_only in V2",
        "next_commands": [
            "python -m certgen.cli.validate_feature_cache --manifest <manifest>",
            "python -m certgen.cli.certify_clean_metric --features-a <a> --features-b <b> --features-r <r> --metric mmd_rbf --method betting ...",
        ],
    }
    write_json(plan, out_json)
    md_lines = [
        "# V2 First Pilot Plan",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"- Evidence status: `{plan['evidence_status']}`",
        f"- Claim status: `{plan['claim_status']}`",
        f"- Selected benchmark: `{plan['selected_benchmark']}`",
        f"- Selected model pairs: `{plan['selected_model_pairs']}`",
        f"- Missing artifacts: `{plan['missing_artifacts']}`",
        "",
        "## Next Commands",
        "",
    ]
    for command in plan["next_commands"]:
        md_lines.append(f"- `{command}`")
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return plan
