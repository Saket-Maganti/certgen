"""R1 CPU validation of the clean-core decision engine on synthetic streams.

This is a METHOD diagnostic, not generative-benchmark evidence. It validates, on
synthetic bounded streams, that the implemented engine behaves as the theory
requires:

  1. Anytime-valid Type-I control: under the null (Delta = 0) the betting CS
     false-decides at most alpha of the time even while monitored at every step,
     whereas naive fixed-n peeking inflates well past alpha.
  2. Power / samples-to-decision: under real gaps the betting CS decides, and it
     decides with fewer units than the union-Hoeffding CS (the compute-savings
     story), with no loss of validity.
  3. e-BH FDR control: across many simultaneous comparisons, e-BH keeps the
     realized false discovery proportion <= alpha and yields a decided/undecided
     split (the audit output) under shared-reference dependence.
  4. Block-size sensitivity: decision time and interval width vs block size on a
     synthetic feature triplet, via the real mmd_difference_stream + betting CS.

All outputs are evidence_status=synthetic_only, claim_allowed=False. The real
generative-benchmark audit numbers require feature caches and remain TBD.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from certgen.analysis.block_size_sensitivity import block_size_sensitivity
from certgen.analysis.samples_to_decision import samples_to_decision_from_states
from certgen.certs.multiple_comparisons import audit_comparisons_with_fdr
from certgen.core.io import write_json
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig
from certgen.stats.e_values import betting_e_value

LOWER, UPPER = -1.0, 1.0


def _bounded_stream(rng: np.random.Generator, mean: float, n: int, sd: float = 0.3) -> list[float]:
    return np.clip(rng.normal(mean, sd, size=n), LOWER, UPPER).tolist()


def _cs_decision(values: list[float], alpha: float, method: str, budget: int) -> tuple[int | None, str | None]:
    cs = confidence_sequence(values, CSConfig(alpha, budget, LOWER, UPPER, method))
    n = samples_to_decision_from_states(cs.states)
    if n is None:
        return None, None
    state = cs.states[n - 1]
    direction = "A" if state["upper"] < 0 else "B" if state["lower"] > 0 else None
    return n, direction


def _naive_peek_decision(values: list[float], budget: int, every: int = 5) -> tuple[int | None, str | None]:
    arr = np.asarray(values)
    for n in range(every, budget + 1, every):
        pre = arr[:n]
        mu = float(pre.mean())
        rad = 1.96 * float(pre.std(ddof=1)) / np.sqrt(n) if n > 1 else np.inf
        if mu + rad < 0:
            return n, "A"
        if mu - rad > 0:
            return n, "B"
    return None, None


def experiment_type_i_and_power(reps: int, budget: int, alpha: float, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    scenarios = {"null_equal_distance": 0.0, "small_effect_A_better": -0.08, "medium_effect_A_better": -0.20}
    methods = ["naive_fixed_n_peek", "betting", "hoeffding"]
    out: dict[str, Any] = {"alpha": alpha, "reps": reps, "budget": budget, "scenarios": {}}
    for sname, mean in scenarios.items():
        agg = {m: {"decided": 0, "false": 0, "stops": []} for m in methods}
        for _ in range(reps):
            values = _bounded_stream(rng, mean, budget)
            for m in methods:
                if m == "naive_fixed_n_peek":
                    stop, direction = _naive_peek_decision(values, budget)
                else:
                    stop, direction = _cs_decision(values, alpha, m, budget)
                if stop is not None:
                    agg[m]["decided"] += 1
                    agg[m]["stops"].append(stop)
                    if mean == 0.0 or direction != "A":
                        agg[m]["false"] += 1
        out["scenarios"][sname] = {
            m: {
                "decided_rate": agg[m]["decided"] / reps,
                "false_decision_rate": agg[m]["false"] / reps,
                "mean_samples_to_decision": float(np.mean(agg[m]["stops"])) if agg[m]["stops"] else None,
                "median_samples_to_decision": float(np.median(agg[m]["stops"])) if agg[m]["stops"] else None,
            }
            for m in methods
        }
    return out


def experiment_ebh_fdr(reps: int, k: int, frac_null: float, budget: int, alpha: float, seed: int, effect: float = -0.20) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    num_null = int(round(k * frac_null))
    truth = ["null"] * num_null + ["effect"] * (k - num_null)
    fdp, power, undecided = [], [], []
    for _ in range(reps):
        comparisons = []
        for i, t in enumerate(truth):
            mean = 0.0 if t == "null" else effect
            values = _bounded_stream(rng, mean, budget)
            e = betting_e_value(values, CSConfig(alpha, budget, LOWER, UPPER, "betting"))
            comparisons.append({"comparison_id": f"c{i}", "e_value": e})
        audit = audit_comparisons_with_fdr(comparisons, alpha)
        decided = {c["comparison_id"] for c in audit["comparisons"] if c["decided_under_fdr"]}
        rejected = [i for i in range(k) if f"c{i}" in decided]
        fdp.append(sum(1 for i in rejected if truth[i] == "null") / len(rejected) if rejected else 0.0)
        effects = [i for i in range(k) if truth[i] == "effect"]
        power.append(sum(1 for i in effects if f"c{i}" in decided) / max(1, len(effects)))
        undecided.append(audit["undecided_fraction"])
    return {
        "k": k,
        "frac_null": frac_null,
        "effect": effect,
        "reps": reps,
        "alpha": alpha,
        "budget": budget,
        "mean_realized_FDP": float(np.mean(fdp)),
        "max_realized_FDP": float(np.max(fdp)),
        "fdr_target_met": bool(np.mean(fdp) <= alpha),
        "mean_power": float(np.mean(power)),
        "mean_undecided_fraction": float(np.mean(undecided)),
    }


def experiment_block_size(seed: int, alpha: float) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    d, n = 32, 2400
    # Reference and model A share a direction; model B is shifted into other
    # coordinates so the gap survives l2-normalization in the bounded RBF kernel.
    base = rng.normal(0.0, 1.0, size=(n, d))
    reference = base.copy()
    reference[:, 0] += 3.0
    model_a = base + rng.normal(0.0, 0.05, size=(n, d))
    model_a[:, 0] += 3.0
    model_b = base.copy()
    model_b[:, 1] += 3.0
    return block_size_sensitivity(model_a, model_b, reference, alpha=alpha, block_sizes=[1, 4, 16, 32], seed=seed)


def run(out_json: str | Path = "data/results/r1_cpu_validation.json", out_md: str | Path = "docs/R1_CPU_VALIDATION.md", *, reps: int = 200, budget: int = 150, alpha: float = 0.05, seed: int = 7) -> dict[str, Any]:
    type_i = experiment_type_i_and_power(reps, budget, alpha, seed)
    ebh = experiment_ebh_fdr(reps, k=20, frac_null=0.5, budget=budget, alpha=alpha, seed=seed + 1)
    block = experiment_block_size(seed + 2, alpha)
    payload = {
        "evidence_status": "synthetic_only",
        "claim_allowed": False,
        "labels": ["method_validation", "not_paper_claim", "not_generative_benchmark_evidence"],
        "type_i_and_power": type_i,
        "ebh_fdr": ebh,
        "block_size_sensitivity": block,
    }
    write_json(payload, out_json)
    _write_report(payload, out_md)
    return payload


def _fmt(value: Any) -> str:
    return "n/a" if value is None else (f"{value:.3f}" if isinstance(value, float) else str(value))


def _write_report(payload: dict[str, Any], out_md: str | Path) -> None:
    alpha = payload["type_i_and_power"]["alpha"]
    lines = [
        "# R1 CPU Validation (synthetic method diagnostic)",
        "",
        "`evidence_status: synthetic_only` `claim_allowed: false` `NO_REAL_EVIDENCE`",
        "",
        "This is a non-claim, synthetic method diagnostic and is not paper evidence (no real result). It validates the implemented engine on synthetic bounded streams; audit numbers on real generative models remain TBD until claim-eligible feature caches exist.",
        "",
        f"## 1. Anytime-valid Type-I control and power (alpha={alpha})",
        "",
        "| scenario | method | decided_rate | false_decision_rate | mean_samples_to_decision |",
        "|---|---|---:|---:|---:|",
    ]
    for sname, methods in payload["type_i_and_power"]["scenarios"].items():
        for m, stats in methods.items():
            lines.append(
                f"| {sname} | {m} | {_fmt(stats['decided_rate'])} | {_fmt(stats['false_decision_rate'])} | {_fmt(stats['mean_samples_to_decision'])} |"
            )
    ebh = payload["ebh_fdr"]
    block = payload["block_size_sensitivity"]
    lines += [
        "",
        "Target: betting/hoeffding `false_decision_rate <= alpha` under the null; naive peeking should exceed it.",
        "",
        f"## 2. e-BH FDR control ({ebh['k']} comparisons, {int(ebh['frac_null']*100)}% null)",
        "",
        f"- mean realized FDP: `{_fmt(ebh['mean_realized_FDP'])}` (target <= {alpha}); met: `{ebh['fdr_target_met']}`",
        f"- mean power on true gaps: `{_fmt(ebh['mean_power'])}`",
        f"- mean undecided fraction: `{_fmt(ebh['mean_undecided_fraction'])}`",
        "",
        "## 3. Block-size sensitivity (synthetic feature triplet)",
        "",
        "| block_size | num_units | decided | samples_to_decision_units | final_width |",
        "|---:|---:|:--:|---:|---:|",
    ]
    for row in block["rows"]:
        lines.append(
            f"| {row['block_size']} | {row['num_units']} | {row['decided']} | {_fmt(row['samples_to_decision_units'])} | {_fmt(row['final_width'])} |"
        )
    lines += ["", "_Synthetic diagnostic only; not real benchmark evidence._", ""]
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run(), indent=2)[:400])
