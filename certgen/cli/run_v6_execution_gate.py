"""Run V6 execution-first gates."""

from __future__ import annotations

import argparse

from certgen.pipeline.v6_execution import (
    run_r1c_feature_extraction_gate,
    run_r1d_metric_reproduction_gate,
    run_r1e_first_pilot_audit,
    write_final_execution_audit,
    write_r2_scale_plan,
    write_r3_multibench_plan,
    write_r4_result_eligibility,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CertGen V6 execution-first gate artifacts.")
    parser.add_argument(
        "--stage",
        required=True,
        choices=["r1c", "r1d", "r1e", "r2", "r3", "r4", "final", "all"],
    )
    parser.add_argument("--feature-dir", default="data/features/cifar10_r1")
    args = parser.parse_args(argv)
    stages = ["r1c", "r1d", "r1e", "r2", "r3", "r4", "final"] if args.stage == "all" else [args.stage]
    payloads = []
    for stage in stages:
        if stage == "r1c":
            payloads.append(run_r1c_feature_extraction_gate())
        elif stage == "r1d":
            payloads.append(run_r1d_metric_reproduction_gate(feature_dir=args.feature_dir))
        elif stage == "r1e":
            payloads.append(run_r1e_first_pilot_audit(feature_dir=args.feature_dir))
        elif stage == "r2":
            payloads.append(write_r2_scale_plan())
        elif stage == "r3":
            payloads.append(write_r3_multibench_plan())
        elif stage == "r4":
            payloads.append(write_r4_result_eligibility())
        elif stage == "final":
            payloads.append(write_final_execution_audit())
    for payload in payloads:
        print(f"{payload.get('stage', args.stage)}: {payload.get('status_code')}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
