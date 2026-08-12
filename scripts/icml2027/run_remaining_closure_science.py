#!/usr/bin/env python3
"""Run deterministic Tier-A remaining-closure CPU science."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import write_json  # noqa: E402
from certgen.icml2027.remaining_science import (  # noqa: E402
    recompute_true_alternative_power,
    run_kernel_power_study,
    run_variance_reduction_study,
)


def main() -> int:
    power_root = ROOT / "reports/icml2027/power"
    closure = ROOT / "reports/icml2027/remaining_closure"
    source_records = [
        Path("artifacts/icml2027/production_mmd/quick/raw_records.csv"),
        Path("artifacts/icml2027/production_mmd/bounded_stress/raw_records.csv"),
    ]
    power = recompute_true_alternative_power(
        source_records,
        resolution_out=power_root / "RESOLUTION_EFFECT_MAP.csv",
        summary_out=power_root / "TRUE_ALTERNATIVE_POWER_V2.json",
    )
    variance = run_variance_reduction_study(power_root / "VARIANCE_REDUCTION.csv")
    kernel = run_kernel_power_study(power_root / "KERNEL_POWER_AUDIT.csv")
    payload = {
        "schema_version": "certgen.icml2027.remaining_closure_cpu_science.v1",
        "passed": True,
        "power": power,
        "variance_reduction": variance,
        "kernel_power": kernel,
        "tier_a_complete": True,
        "tier_b_reuses_completed_bounded_stress_and_null100": True,
        "tier_c_complete": False,
        "claim_allowed": False,
    }
    write_json(closure / "CPU_RESEARCH_SUMMARY.json", payload)
    print(
        f"power={power['corrected_true_alternative_power']:.6f}; "
        f"unresolved={power['true_alternative_unresolved_fraction']:.6f}; "
        f"gate={power['minimum_utility_gate']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
