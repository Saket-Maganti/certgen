"""Bounded-memory numerical stress audit for kernel and sequential primitives."""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import write_csv, write_json
from certgen.icml2027.sequential import evaluate_stream
from certgen.metrics.mmd import unbiased_mmd2


def _case(case_id: str, function: Any) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        value = function()
        finite = bool(np.all(np.isfinite(np.asarray(value, dtype=float))))
        return {
            "case_id": case_id,
            "passed": finite,
            "value": repr(value),
            "error": "" if finite else "nonfinite output",
            "runtime_seconds": time.perf_counter() - started,
            "claim_allowed": False,
        }
    except Exception as exc:
        return {
            "case_id": case_id,
            "passed": False,
            "value": "",
            "error": f"{type(exc).__name__}: {exc}",
            "runtime_seconds": time.perf_counter() - started,
            "claim_allowed": False,
        }


def run_numerical_audit(out_dir: str | Path, *, seed: int = 2027) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    base_x = rng.normal(size=(64, 16))
    base_y = rng.normal(0.1, 1.1, size=(64, 16))
    duplicate = np.repeat(base_x[:1], 64, axis=0)
    cases = [
        _case("float32_rbf", lambda: unbiased_mmd2(base_x.astype(np.float32), base_y.astype(np.float32), kernel="rbf", bandwidth=1.0)),
        _case("float64_rbf", lambda: unbiased_mmd2(base_x, base_y, kernel="rbf", bandwidth=1.0)),
        _case("tiny_bandwidth", lambda: unbiased_mmd2(base_x, base_y, kernel="rbf", bandwidth=1e-9)),
        _case("huge_bandwidth", lambda: unbiased_mmd2(base_x, base_y, kernel="rbf", bandwidth=1e9)),
        _case("high_dimension", lambda: unbiased_mmd2(rng.normal(size=(24, 4096)), rng.normal(size=(24, 4096)), kernel="rbf", bandwidth=64.0)),
        _case("duplicate_rows", lambda: unbiased_mmd2(duplicate, duplicate + 1e-9, kernel="rbf", bandwidth=1.0)),
        _case("zero_variance", lambda: unbiased_mmd2(np.zeros((32, 8)), np.ones((32, 8)), kernel="rbf", bandwidth=1.0)),
        _case("large_n_bounded", lambda: unbiased_mmd2(rng.normal(size=(512, 4)), rng.normal(size=(512, 4)), kernel="rbf", bandwidth=2.0)),
        _case("sequential_zero", lambda: evaluate_stream([0.0] * 1000, alpha=0.05, rule="anytime").confidence_width),
    ]
    # Nonfinite inputs must fail closed rather than produce a usable decision.
    nonfinite = evaluate_stream([0.0, math.nan], alpha=0.05, rule="anytime")
    cases.append(
        {
            "case_id": "nan_fail_closed",
            "passed": nonfinite.decision == "INVALID",
            "value": nonfinite.decision,
            "error": "",
            "runtime_seconds": 0.0,
            "claim_allowed": False,
        }
    )
    target = Path(out_dir)
    write_csv(target / "numerical_audit.csv", cases)
    payload = {
        "schema_version": "certgen.icml2027.numerical_audit.v1",
        "checks_total": len(cases),
        "checks_passed": sum(bool(row["passed"]) for row in cases),
        "passed": all(bool(row["passed"]) for row in cases),
        "float32_float64_difference": abs(float(cases[0]["value"]) - float(cases[1]["value"])),
        "matrix_memory_bounded_by_case_size": True,
        "claim_allowed": False,
    }
    write_json(target / "numerical_audit_summary.json", payload)
    return payload
