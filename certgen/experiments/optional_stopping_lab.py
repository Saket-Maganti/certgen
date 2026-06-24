"""Synthetic optional-stopping lab for V2 smoke validation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.io import write_json
from certgen.reporting.optional_stopping_report import render_optional_stopping_report
from certgen.stats.design_contracts import CSConfig
from certgen.stats.cs import confidence_sequence


def _naive_ci_decision(prefix: np.ndarray, alpha: float) -> str:
    n = len(prefix)
    mean = float(prefix.mean())
    sd = float(prefix.std(ddof=1)) if n > 1 else 1.0
    radius = 1.96 * sd / max(1.0, np.sqrt(n))
    if mean + radius < 0:
        return "A"
    if mean - radius > 0:
        return "B"
    return "none"


def _threshold_decision(prefix: np.ndarray, threshold: float = 0.15) -> str:
    mean = float(prefix.mean())
    if mean < -threshold:
        return "A"
    if mean > threshold:
        return "B"
    return "none"


def _monitor(values: np.ndarray, alpha: float, method: str) -> tuple[str, int | None]:
    for n in range(2, len(values) + 1):
        prefix = values[:n]
        if method == "naive_fixed_width_ci":
            decision = _naive_ci_decision(prefix, alpha)
        else:
            decision = _threshold_decision(prefix)
        if decision != "none":
            return decision, n
    return "none", None


def _cs_monitor(values: np.ndarray, alpha: float, method: str) -> tuple[str, int | None]:
    for n in range(2, len(values) + 1):
        result = confidence_sequence(
            values[:n].astype(float).tolist(),
            CSConfig(alpha=alpha, budget_units=n, lower_bound=-1.0, upper_bound=1.0, method=method),
        )
        if result.upper < 0:
            return "A", n
        if result.lower > 0:
            return "B", n
    return "none", None


def run_optional_stopping_lab(
    *,
    out_dir: str | Path,
    num_replicates: int = 200,
    budget: int = 200,
    alpha: float = 0.05,
    seed: int = 0,
    evidence_status: str = "smoke_only",
) -> dict[str, Any]:
    if evidence_status not in {"smoke_only", "demo_only"}:
        raise ValueError("synthetic optional-stopping lab only supports smoke/demo evidence statuses")
    rng = np.random.default_rng(seed)
    scenarios = {
        "null": 0.0,
        "negative_A_better": -0.25,
        "positive_B_better": 0.25,
        "near_zero": 0.03,
    }
    methods = ["naive_fixed_width_ci", "naive_running_mean_threshold", "v2_hoeffding_cs", "v2_empirical_bernstein_cs"]
    summary: dict[str, Any] = {
        "label": "SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE",
        "evidence_status": evidence_status,
        "num_replicates": num_replicates,
        "budget": budget,
        "alpha": alpha,
        "seed": seed,
        "scenarios": {},
    }
    for scenario, mean in scenarios.items():
        scenario_rows = {method: {"decisions": 0, "false_decisions": 0, "sample_units": []} for method in methods}
        for _ in range(num_replicates):
            values = np.clip(rng.normal(mean, 0.35, size=budget), -1.0, 1.0)
            for method in methods:
                if method == "v2_hoeffding_cs":
                    decision, n = _cs_monitor(values, alpha, "hoeffding")
                elif method == "v2_empirical_bernstein_cs":
                    decision, n = _cs_monitor(values, alpha, "empirical_bernstein")
                else:
                    decision, n = _monitor(values, alpha, method)
                if decision != "none":
                    scenario_rows[method]["decisions"] += 1
                    scenario_rows[method]["sample_units"].append(n)
                    if scenario == "null":
                        scenario_rows[method]["false_decisions"] += 1
                    elif scenario == "negative_A_better" and decision != "A":
                        scenario_rows[method]["false_decisions"] += 1
                    elif scenario == "positive_B_better" and decision != "B":
                        scenario_rows[method]["false_decisions"] += 1
        rendered: dict[str, Any] = {}
        for method, stats in scenario_rows.items():
            sample_units = stats["sample_units"]
            rendered[method] = {
                "decision_rate": stats["decisions"] / num_replicates,
                "false_decision_rate": stats["false_decisions"] / num_replicates,
                "average_sample_units_to_decision": float(np.mean(sample_units)) if sample_units else None,
            }
        summary["scenarios"][scenario] = rendered

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(summary, out_dir / "summary.json")
    report = render_optional_stopping_report(summary)
    Path("docs").mkdir(exist_ok=True)
    Path("docs/V2_OPTIONAL_STOPPING_LAB.md").write_text(report, encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a V2 synthetic optional-stopping smoke lab.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--num-replicates", type=int, default=200)
    parser.add_argument("--budget", type=int, default=200)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--evidence-status", default="smoke_only")
    args = parser.parse_args(argv)
    run_optional_stopping_lab(
        out_dir=args.out_dir,
        num_replicates=args.num_replicates,
        budget=args.budget,
        alpha=args.alpha,
        seed=args.seed,
        evidence_status=args.evidence_status,
    )
    print(f"Wrote optional-stopping smoke lab outputs to {args.out_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
