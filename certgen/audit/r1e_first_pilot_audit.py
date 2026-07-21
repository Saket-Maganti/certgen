"""CLI wrapper for the R1E first-pilot audit."""

from __future__ import annotations

import argparse

from certgen.pipeline.v6_execution import run_r1e_first_pilot_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the R1E first certificate pilot audit.")
    parser.add_argument("--feature-dir", default="data/features/cifar10_r1")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--r1d-json-out", default="data/results/r1d_metric_reproduction.json")
    parser.add_argument("--r1d-report", default="docs/R1D_METRIC_REPRODUCTION_REPORT.md")
    parser.add_argument("--pilot-report", default="docs/R1E_FIRST_CERTIFICATE_PILOT_REPORT.md")
    parser.add_argument("--fraction-json", default="data/results/r1e_undecided_fraction.json")
    parser.add_argument("--cert-dir", default="data/results/r1e_clean_core_certificates")
    parser.add_argument("--feature-split-dir", default="data/results/r1e_feature_splits")
    args = parser.parse_args(argv)
    payload = run_r1e_first_pilot_audit(
        feature_dir=args.feature_dir,
        out=args.out,
        json_out=args.json_out,
        r1d_out_json=args.r1d_json_out,
        r1d_report=args.r1d_report,
        pilot_report=args.pilot_report,
        fraction_json=args.fraction_json,
        cert_dir=args.cert_dir,
        feature_split_dir=args.feature_split_dir,
    )
    print(f"R1E first pilot audit: {'passed' if payload['passed'] else 'failed'} ({payload['status_code']})")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
