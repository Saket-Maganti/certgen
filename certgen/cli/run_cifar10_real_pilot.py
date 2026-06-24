"""CLI for the R1 CIFAR-10 real-pilot readiness path."""

from __future__ import annotations

import argparse

from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or validate the CERTGEN_R1_CIFAR10_REAL_PILOT path.")
    parser.add_argument("--provenance-ledger", required=True)
    parser.add_argument("--sample-manifest", required=True)
    parser.add_argument("--preprocessing-lock", required=True)
    parser.add_argument("--feature-cache-dir", required=True)
    parser.add_argument("--metric-reproduction-audit", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--allow-missing-local-files", action="store_true")
    args = parser.parse_args(argv)
    payload = run_cifar10_r1_readiness(
        provenance_ledger=args.provenance_ledger,
        sample_manifest=args.sample_manifest,
        preprocessing_lock=args.preprocessing_lock,
        feature_cache_dir=args.feature_cache_dir,
        metric_reproduction_audit=args.metric_reproduction_audit,
        out_json=args.out_json,
        report=args.report,
        require_local_files=not args.allow_missing_local_files,
    )
    print(f"CIFAR-10 R1 status: {payload['status']}")
    return 0 if payload["ready_for_r1"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
