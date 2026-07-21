"""Batch certificate runner for V4 synthetic/validated feature paths."""

from __future__ import annotations

from pathlib import Path

from certgen.certs.api import certify_clean_metric_comparison
from certgen.certs.multiple_comparisons import allocate_alpha
from certgen.core.io import read_json, write_json
from certgen.stats.dependence_diagnostics import dependence_warnings


def run_batch_certificates(config: dict, out_json: str | Path, report: str | Path) -> dict:
    comparisons = config.get("comparisons", [])
    metrics = config.get("metrics", ["mmd_rbf"])
    family_size = max(1, len(comparisons) * len(metrics))
    policy = allocate_alpha(float(config.get("alpha", 0.05)), family_size, config.get("alpha_policy", "bonferroni"))
    policy["family_size"] = family_size
    policy["family_definition"] = "cartesian product of predeclared comparisons and metrics in this batch"
    dep = dependence_warnings(comparisons)
    rows = []
    for comp in comparisons:
        for metric in metrics:
            cert_path = Path(out_json).parent / "certificates" / f"{comp['comparison_id']}_{metric}.json"
            cert = certify_clean_metric_comparison(
                comp["features_a"],
                comp["features_b"],
                comp["features_r"],
                metric,
                {},
                {
                    "alpha": policy["alpha_used"],
                    "budget_units": int(config.get("budget_units", 20)),
                    "method": config.get("method", "hoeffding"),
                    "seed": int(comp.get("seed", config.get("seed", 0))),
                    "block_size": config.get("block_size"),
                },
                comp["comparison_id"],
                config.get("evidence_status", "synthetic_only"),
                str(cert_path),
            )
            rows.append(
                {
                    "comparison_id": comp["comparison_id"],
                    "metric_name": metric,
                    "alpha_policy": policy["policy"],
                    "alpha_used": policy["alpha_used"],
                    "n_max": config.get("budget_units", 20),
                    "n_decision": cert.sample_units_seen if cert.decision != "not_decided_at_budget" else None,
                    "decision": cert.decision.replace("A_certified_better", "A_better").replace("B_certified_better", "B_better").replace("not_decided_at_budget", "undecided"),
                    "cs_lower": cert.lower,
                    "cs_upper": cert.upper,
                    "adjusted_for_multiplicity": policy["adjusted_for_multiplicity"],
                    "dependence_warning": dep.get(comp["comparison_id"], []),
                    "evidence_status": config.get("evidence_status", "synthetic_only"),
                    "claim_allowed": False,
                    "seed": comp.get("seed", config.get("seed", 0)),
                }
            )
    payload = {"rows": rows, "multiple_comparison_policy": policy, "claim_allowed": False, "evidence_status": config.get("evidence_status", "synthetic_only")}
    write_json(payload, out_json)
    lines = ["# V4 Batch Certificate Report", "", "`NO_REAL_EVIDENCE`", "", f"Policy: `{policy['policy']}`", "", "| Comparison | Metric | Decision | Alpha | Dependence |", "|---|---|---|---:|---|"]
    for row in rows:
        lines.append(f"| `{row['comparison_id']}` | `{row['metric_name']}` | `{row['decision']}` | {row['alpha_used']} | `{row['dependence_warning']}` |")
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def run_batch_from_file(config_path: str | Path, out_json: str | Path, report: str | Path) -> dict:
    return run_batch_certificates(read_json(config_path), out_json, report)
