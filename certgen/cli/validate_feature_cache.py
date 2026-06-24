"""Validate V2 or V3 feature-cache manifests."""

from __future__ import annotations

import argparse

from certgen.features.validate_cache import validate_feature_cache_manifest
from certgen.features.cache_validate import validate_v3_feature_cache, write_v3_feature_cache_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a CertGen feature-cache manifest.")
    parser.add_argument("--manifest")
    parser.add_argument("--features")
    parser.add_argument("--sidecar")
    parser.add_argument("--out")
    parser.add_argument("--json-out")
    parser.add_argument("--strict-hash", action="store_true")
    parser.add_argument("--metric")
    args = parser.parse_args(argv)
    if args.features or args.sidecar:
        if not (args.features and args.sidecar and args.out and args.json_out):
            parser.error("--features/--sidecar mode requires --out and --json-out")
        result = validate_v3_feature_cache(features_path=args.features, sidecar_path=args.sidecar, strict_hash=args.strict_hash, metric=args.metric)
        write_v3_feature_cache_report(result, args.out, args.json_out)
        if not result.passed:
            for error in result.errors:
                print(f"ERROR: {error}")
            return 1
        print(f"Feature cache V3 valid: {args.features}")
        return 0
    if not args.manifest:
        parser.error("--manifest or --features/--sidecar is required")
    errors = validate_feature_cache_manifest(args.manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Feature cache manifest valid: {args.manifest}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
