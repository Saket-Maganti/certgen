"""CLI for V2 clean metric certificates over feature arrays."""

from __future__ import annotations

import argparse
import json

from certgen.certs.api import certify_clean_metric_comparison


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a V2 clean-core certificate from feature arrays.")
    parser.add_argument("--features-a", required=True)
    parser.add_argument("--features-b", required=True)
    parser.add_argument("--features-r", required=True)
    parser.add_argument("--metric", required=True, choices=["mmd_rbf", "cmmd_clip_mmd", "kid_polynomial"])
    parser.add_argument("--comparison-id", required=True)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--budget-units", type=int, required=True)
    parser.add_argument("--clip-lower", type=float, default=None, help="Legacy ignored flag; certified bounds come from the kernel.")
    parser.add_argument("--clip-upper", type=float, default=None, help="Legacy ignored flag; certified bounds come from the kernel.")
    parser.add_argument("--method", default="hoeffding", choices=["hoeffding", "betting", "empirical_bernstein"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--block-size", type=int, default=None)
    parser.add_argument("--metric-reproduction-audit", default=None)
    parser.add_argument("--reference-draw-plan", default=None)
    parser.add_argument("--out", required=True)
    parser.add_argument("--evidence-status", default="smoke_only")
    parser.add_argument("--kernel-config-json", default=None)
    args = parser.parse_args(argv)
    kernel_config = json.loads(args.kernel_config_json) if args.kernel_config_json else {}
    cert = certify_clean_metric_comparison(
        features_a_path=args.features_a,
        features_b_path=args.features_b,
        features_r_path=args.features_r,
        metric_label=args.metric,
        kernel_config=kernel_config,
        cs_config={
            "alpha": args.alpha,
            "budget_units": args.budget_units,
            "method": args.method,
            "seed": args.seed,
            "block_size": args.block_size,
            "metric_reproduction_audit": args.metric_reproduction_audit,
            "reference_draw_plan": args.reference_draw_plan,
        },
        comparison_id=args.comparison_id,
        evidence_status=args.evidence_status,
        out_path=args.out,
    )
    print(f"Wrote V2 clean certificate: {args.out}; decision={cert.decision}; evidence_status={cert.evidence_status}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
