#!/usr/bin/env python3
"""Execute every safe CPU-only scientific closure rehearsal and benchmark."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import write_json  # noqa: E402
from certgen.icml2027.final_fixture import run_full_fixture_rehearsal  # noqa: E402
from certgen.icml2027.scientific_closure import (  # noqa: E402
    run_cifar10k_cpu_feasibility,
    run_independent_mmd_audit,
    run_normalization_power_audit,
)


def main() -> int:
    fixture_root = ROOT / "artifacts/icml2027/final_closure_fixture"
    fixture = run_full_fixture_rehearsal(fixture_root, repo_root=ROOT)
    normalization = run_normalization_power_audit(
        source_records=ROOT / "artifacts/icml2027/production_mmd/quick/raw_records.csv",
        out_dir=ROOT / "reports/icml2027/production_mmd",
    )
    independent = run_independent_mmd_audit(
        ROOT / "reports/icml2027/final_closure/INDEPENDENT_MMD_REPRODUCTION.json"
    )
    feasibility = run_cifar10k_cpu_feasibility(
        ROOT / "reports/icml2027/final_closure/CIFAR10K_CPU_FEASIBILITY.csv",
        payload_index=fixture_root / "generation/generation_payload.output.index.json",
    )
    payload = {
        "schema_version": "certgen.icml2027.final_closure_cpu_science.v1",
        "passed": all(row["passed"] for row in (fixture, normalization, independent, feasibility)),
        "fixture": fixture,
        "normalization_power": normalization,
        "independent_mmd": independent,
        "feasibility": feasibility,
        "claim_allowed": False,
    }
    write_json(ROOT / "reports/icml2027/final_closure/CPU_SCIENCE_SUMMARY.json", payload)
    print(f"passed={payload['passed']}")
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
