"""V3 optional-stopping lab."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.io import write_json
from certgen.reporting.optional_stopping_report import render_optional_stopping_report
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


def _load_config(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".json":
        import json

        return json.loads(text)
    import yaml

    return yaml.safe_load(text)


def run_optional_stopping_lab_v3(config_path: str | Path, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    cfg = _load_config(config_path)
    rng = np.random.default_rng(int(cfg.get("seed", 0)))
    reps = int(cfg.get("num_replicates", 20))
    budget = int(cfg.get("budget", 80))
    alpha = float(cfg.get("alpha", 0.05))
    scenarios = {
        "null_equal_distance": 0.0,
        "small_effect_A_better": -0.08,
        "medium_effect_A_better": -0.25,
        "heavy_tailed_bounded": 0.0,
    }
    methods = ["naive_fixed_n_peek", "naive_running_mean_threshold", "certgen_hoeffding_cs", "certgen_empirical_bernstein_cs"]
    output = {"evidence_status": "synthetic_only", "claim_allowed": False, "scenarios": {}, "num_replicates": reps, "budget": budget, "alpha": alpha}
    for name, mean in scenarios.items():
        method_stats = {m: {"decisions": 0, "false_decisions": 0, "stopping_times": []} for m in methods}
        for _ in range(reps):
            if name == "heavy_tailed_bounded":
                values = np.clip(rng.standard_t(3, size=budget) * 0.2, -1, 1)
            else:
                values = np.clip(rng.normal(mean, 0.3, size=budget), -1, 1)
            for method in methods:
                decision = "none"
                stop = None
                peek_points = range(5, budget + 1, 5)
                for n in peek_points:
                    prefix = values[:n]
                    m = float(prefix.mean())
                    if method == "naive_fixed_n_peek":
                        radius = 1.96 * float(prefix.std(ddof=1)) / max(1, n**0.5)
                        decision = "A" if m + radius < 0 else "B" if m - radius > 0 else "none"
                    elif method == "naive_running_mean_threshold":
                        decision = "A" if m < -0.15 else "B" if m > 0.15 else "none"
                    else:
                        cs_method = "hoeffding" if method == "certgen_hoeffding_cs" else "empirical_bernstein"
                        cs = confidence_sequence(prefix.tolist(), CSConfig(alpha, n, -1, 1, cs_method))
                        decision = "A" if cs.upper < 0 else "B" if cs.lower > 0 else "none"
                    if decision != "none":
                        stop = n
                        break
                if decision != "none":
                    method_stats[method]["decisions"] += 1
                    method_stats[method]["stopping_times"].append(stop)
                    if name.startswith("null") or name == "heavy_tailed_bounded":
                        method_stats[method]["false_decisions"] += 1
                    elif decision != "A":
                        method_stats[method]["false_decisions"] += 1
        rendered = {}
        for method, stats in method_stats.items():
            stops = stats["stopping_times"]
            rendered[method] = {
                "decision_rate": stats["decisions"] / reps,
                "false_decision_rate": stats["false_decisions"] / reps,
                "average_samples_to_decision": float(np.mean(stops)) if stops else None,
                "average_sample_units_to_decision": float(np.mean(stops)) if stops else None,
                "stopping_times": stops,
            }
        output["scenarios"][name] = rendered
    report = render_optional_stopping_report({"evidence_status": "synthetic_only", "num_replicates": reps, "budget": budget, "alpha": alpha, "scenarios": output["scenarios"]})
    report += "\nThis synthetic method diagnostic is not real benchmark evidence.\n"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(report, encoding="utf-8")
    write_json(output, json_out)
    return output
