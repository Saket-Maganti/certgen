#!/usr/bin/env python3
"""Build an identity-complete ICML generation or feature worker specification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import file_sha256, stable_hash, write_json  # noqa: E402
from certgen.icml2027.execution_contract import (  # noqa: E402
    build_dinov2_preflight_worker_spec,
    build_feature_worker_spec,
    build_generation_worker_spec,
    validate_generation_job_partition,
    validate_worker_spec,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lane",
        choices=[
            "dinov2_preflight",
            "cifar_10k_generation",
            "cifar_10k_features",
            "dinov2_features",
            "released_sample_features",
        ],
        required=True,
    )
    parser.add_argument("--authenticated-prerequisite-set-sha256", required=True)
    parser.add_argument("--asset-contract")
    parser.add_argument("--asset-manifest")
    parser.add_argument("--asset-root")
    parser.add_argument("--feature-contract")
    parser.add_argument("--shard-size", type=int, default=500)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    seed_manifest = json.loads(
        (ROOT / "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json").read_text(
            encoding="utf-8"
        )
    )
    contract = json.loads(
        (ROOT / "registry/icml2027/cifar_10k_v2_execution_contract_v1.json").read_text(
            encoding="utf-8"
        )
    )
    if args.lane == "dinov2_preflight":
        if not args.asset_manifest or not args.asset_root:
            parser.error("dinov2_preflight requires --asset-manifest and --asset-root")
        from certgen.icml2027.dinov2 import validate_asset_manifest

        asset_manifest = Path(args.asset_manifest)
        asset_root = Path(args.asset_root).resolve()
        asset_validation = validate_asset_manifest(asset_manifest, asset_root)
        if not asset_validation["passed"]:
            parser.error(
                "DINO asset/license validation failed: "
                + "; ".join(asset_validation["errors"])
            )
        inventory = [
            {
                "path": path.relative_to(asset_root).as_posix(),
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(asset_root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        ]
        spec = build_dinov2_preflight_worker_spec(
            input_package_sha256=args.authenticated_prerequisite_set_sha256,
            asset_manifest_sha256=file_sha256(asset_manifest),
            asset_inventory_sha256=stable_hash(inventory),
            root=ROOT,
        )
        scientific_contract = None
        partition = {"passed": True, "errors": []}
    elif args.lane == "cifar_10k_generation":
        if not args.asset_contract:
            parser.error("cifar_10k_generation requires --asset-contract")
        asset_requirements = json.loads(Path(args.asset_contract).read_text(encoding="utf-8"))
        spec = build_generation_worker_spec(
            seed_manifest,
            contract,
            input_package_sha256=args.authenticated_prerequisite_set_sha256,
            asset_requirements=asset_requirements,
            shard_size=args.shard_size,
        )
        scientific_contract = contract
        partition = validate_generation_job_partition(spec["jobs"], seed_manifest)
    else:
        if not args.feature_contract:
            parser.error("feature lanes require --feature-contract")
        feature = json.loads(Path(args.feature_contract).read_text(encoding="utf-8"))
        scientific_identity = feature["scientific_identity"]
        spec = build_feature_worker_spec(
            lane=args.lane,
            input_package_sha256=args.authenticated_prerequisite_set_sha256,
            study_id=scientific_identity["study_id"],
            study_hash=scientific_identity["study_hash"],
            configuration_sha256=scientific_identity["configuration_sha256"],
            seed_plan_sha256=scientific_identity["seed_plan_sha256"],
            sample_identity_policy_sha256=scientific_identity["sample_identity_policy_sha256"],
            source_manifests=feature["source_manifests"],
            extractor_specs=feature["extractor_specs"],
            shards_per_source=int(feature["shards_per_source"]),
            reference_plan_sha256=scientific_identity.get("reference_plan_sha256"),
            expected_prefix_hashes=scientific_identity.get("expected_prefix_hashes", {}),
            model_revisions=scientific_identity.get("model_revisions", {}),
            output_schema_version=scientific_identity.get(
                "output_schema_version", "certgen.icml2027.feature_payload.v1"
            ),
        )
        scientific_contract = contract if args.lane == "cifar_10k_features" else None
        partition = {"passed": True, "errors": []}
    scientific = validate_worker_spec(
        spec,
        expected_lane=args.lane,
        contract=scientific_contract,
    )
    if not scientific["passed"] or not partition["passed"]:
        raise RuntimeError("refusing to write an invalid worker specification")
    write_json(args.out, spec)
    print(f"jobs={len(spec['jobs'])}; claim_allowed=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
