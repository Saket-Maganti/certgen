"""First-benchmark V3 pilot orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.certs.api import certify_clean_metric_comparison
from certgen.core.io import write_json
from certgen.features.cache_validate import validate_v3_feature_cache
from certgen.reporting.pilot_cards import render_pilot_report


def _load_config(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".json":
        import json

        return json.loads(text)
    import yaml

    return yaml.safe_load(text)


def run_first_pilot(pilot_config: str | Path, out_dir: str | Path, report: str | Path, json_out: str | Path) -> dict[str, Any]:
    config = _load_config(pilot_config)
    mode = config.get("mode", "dry_run")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "pilot_id": config.get("pilot_id", "first_pilot_v3"),
        "mode": mode,
        "evidence_status": "dry_run_only" if mode == "dry_run" else "real_pilot_non_claim",
        "claim_allowed": False,
        "claim_blockers": ["V3 pilot defaults to non-claim mode"],
        "comparisons": [],
        "certificates": [],
        "pilot_result_computed": False,
        "paper_claim_allowed": False,
        "undecided_fraction": None,
    }
    if mode == "dry_run":
        for comp in config.get("comparisons", []):
            summary["comparisons"].append({"comparison_id": comp.get("comparison_id"), "status": "planned", "missing_artifacts": []})
    elif mode == "real_features":
        ref = config["reference_cache"]
        ref_validation = validate_v3_feature_cache(features_path=ref["npz"], sidecar_path=ref["sidecar"], strict_hash=False, allow_constant=True)
        valid_results = []
        for comp in config.get("comparisons", []):
            a = comp["model_a_cache"]
            b = comp["model_b_cache"]
            a_val = validate_v3_feature_cache(features_path=a["npz"], sidecar_path=a["sidecar"], strict_hash=False, allow_constant=True)
            b_val = validate_v3_feature_cache(features_path=b["npz"], sidecar_path=b["sidecar"], strict_hash=False, allow_constant=True)
            comp_summary = {"comparison_id": comp["comparison_id"], "feature_cache_valid": ref_validation.passed and a_val.passed and b_val.passed}
            summary["comparisons"].append(comp_summary)
            if comp_summary["feature_cache_valid"]:
                for metric in config.get("metrics", ["mmd_rbf"]):
                    if metric.lower().startswith("fid"):
                        summary["certificates"].append({"metric": metric, "status": "descriptive_only"})
                        continue
                    if metric in {"kid", "kid_polynomial", "kid_poly"}:
                        summary["certificates"].append({"metric": metric, "status": "descriptive_only", "reason": "polynomial KID is not certified by default"})
                        continue
                    metric_label = "cmmd_clip_mmd" if metric in {"cmmd", "cmmd_clip_mmd"} else "mmd_rbf"
                    metric_reproduction_audit = config.get("metric_reproduction_audit")
                    if not metric_reproduction_audit:
                        summary["certificates"].append({"metric": metric_label, "status": "blocked", "reason": "metric reproduction audit required before real-pilot certificate"})
                        continue
                    cert_path = out_dir / "certificates" / f"{comp['comparison_id']}_{metric_label}.json"
                    cert = certify_clean_metric_comparison(
                        a["npz"],
                        b["npz"],
                        ref["npz"],
                        metric_label,
                        {},
                        {
                            "alpha": float(config.get("alpha", 0.05)),
                            "budget_units": int(config.get("max_samples", 40)),
                            "method": config.get("method", "betting"),
                            "seed": int(config.get("seed", 0)),
                            "block_size": config.get("block_size"),
                            "metric_reproduction_audit": metric_reproduction_audit,
                        },
                        comp["comparison_id"],
                        "real_pilot_non_claim",
                        str(cert_path),
                    )
                    summary["certificates"].append({"path": str(cert_path), "decision": cert.decision, "metric": metric_label})
                    valid_results.append(cert.decision)
        summary["pilot_result_computed"] = bool(valid_results)
        if valid_results and all(item in {"A_certified_better", "B_certified_better", "not_decided_at_budget"} for item in valid_results):
            summary["undecided_fraction"] = valid_results.count("not_decided_at_budget") / len(valid_results)
    else:
        raise ValueError("mode must be dry_run or real_features")
    write_json(summary, json_out)
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text(render_pilot_report(summary), encoding="utf-8")
    return summary
