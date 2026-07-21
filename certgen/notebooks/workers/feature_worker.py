"""One-GPU feature worker bound to preflight-approved local snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.extractor_adapters import adapter_for_extractor, package_versions_for
from certgen.cvpr.image_manifest import read_image_manifest, role_id_for_row
from certgen.features.protocol_checks import repeated_batching_check
from certgen.notebooks.network_policy import network_policy_from_config
from certgen.notebooks.worker_contract import completion_identity_fields
from certgen.notebooks.workers.common import hardware_record, load_configuration, require_gpu_pin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--extractor-id", required=True)
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--image-manifest", required=True)
    parser.add_argument("--image-root")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    require_gpu_pin()
    config = load_configuration(args.config)
    network = network_policy_from_config(config)
    if network.model_asset_network_allowed:
        raise RuntimeError("feature extraction requires preflighted offline extractor assets")
    extractor = next(
        (row for row in config["extractors"] if row["feature_space_id"] == args.extractor_id),
        None,
    )
    if extractor is None:
        raise ValueError(f"extractor absent from configuration: {args.extractor_id}")
    asset = json.loads(Path(args.asset_manifest).read_text(encoding="utf-8"))
    if not isinstance(asset, dict) or asset.get("model_or_extractor_id") != args.extractor_id:
        raise ValueError("asset manifest does not match extractor")
    torch, hardware = hardware_record(str(config["configuration_hash"]), args.shard_id)
    packages = package_versions_for(args.extractor_id, str(torch.__version__))
    adapter = adapter_for_extractor(extractor)
    adapter.load(asset, args.cache_root, "cuda:0")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    contract = adapter.contract_report(packages, difference_report=out / "preprocessing_difference.json")
    package_root = Path(args.config).resolve().parent
    if args.image_root:
        image_root = Path(args.image_root)
    elif config.get("feature_input_mode") == "EMBED_IMAGES_IN_PACKAGE":
        image_root = package_root
    else:
        raise ValueError("external feature dataset requires a runtime-resolved --image-root")
    rows = read_image_manifest(args.image_manifest, root=image_root, decode=True)
    roles = {str(row["role"]) for row in rows}
    model_ids = {str(row["model_id"]) for row in rows}
    if len(roles) != 1 or len(model_ids) != 1:
        raise ValueError("feature shards must not mix roles or model IDs")
    features: list[np.ndarray] = []
    sample_ids: list[str] = []
    batch_size = int(extractor["batch_size"])
    with torch.inference_mode():
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            images = []
            for row in batch:
                path = image_root / row["relative_image_path"]
                with Image.open(path) as image:
                    images.append(image.convert("RGB").copy())
            output = adapter.extract_batch(images)
            matrix = output.float().cpu().numpy()
            if matrix.shape != (len(batch), int(extractor["expected_dimension"])):
                raise ValueError(
                    f"extractor output mismatch: expected {(len(batch), int(extractor['expected_dimension']))}, got {matrix.shape}"
                )
            if not np.isfinite(matrix).all():
                raise ValueError("extractor output contains nonfinite values")
            features.append(matrix)
            sample_ids.extend(str(row["sample_id"]) for row in batch)
    matrix = np.concatenate(features, axis=0)
    protocol_rows = rows[: min(8, len(rows))]
    if len(protocol_rows) < 4 or batch_size < 2:
        raise ValueError(
            "feature protocol validation requires at least four rows and a validated batch size >= 2"
        )
    protocol_images = []
    for row in protocol_rows:
        path = image_root / row["relative_image_path"]
        with Image.open(path) as image:
            protocol_images.append(image.convert("RGB").copy())
    with torch.inference_mode():
        batching_check = repeated_batching_check(
            extract_batch=adapter.extract_batch,
            images=protocol_images,
            sample_ids=[str(row["sample_id"]) for row in protocol_rows],
            batch_sizes=(1, min(batch_size, len(protocol_rows))),
            expected_dimension=int(extractor["expected_dimension"]),
            gamma=float((config.get("kernel") or {}).get("gamma", 0.5)),
        )
    if not batching_check["passed"]:
        raise ValueError("repeated-batching protocol validation failed")
    np.savez_compressed(out / "features.npz", features=matrix, sample_ids=np.array(sample_ids))
    output_definition = adapter.output_definition()
    role_id = role_id_for_row(rows[0])
    sidecar = {
        "schema_version": "certgen.feature_shard.v2",
        "extractor_id": args.extractor_id,
        "extractor_revision": extractor["revision"],
        "configuration_hash": config["configuration_hash"],
        "preprocessing_hash": stable_hash_json(extractor["expected_preprocessing"]),
        "array_sha256": file_sha256(out / "features.npz"),
        "rows": len(sample_ids),
        "dimension": int(matrix.shape[1]),
        "sample_order_hash": stable_hash_json(sample_ids),
        "role": role_id,
        "canonical_role": next(iter(roles)),
        "model_id": next(iter(model_ids)),
        "source_manifest_hash": file_sha256(args.image_manifest),
        "source_image_manifest_schema": "certgen.cvpr.image_manifest.v1",
        "expected_preprocessing": extractor["expected_preprocessing"],
        "requested_contract": contract["requested_contract"],
        "observed_contract": contract["observed_contract"],
        "feature_definition": output_definition,
        "resolved_model_id": extractor["model_identifier"],
        "resolved_revision": extractor["revision"],
        "validated_snapshot_path": str(adapter.snapshot_path),
        "asset_manifest_sha256": file_sha256(args.asset_manifest),
        "preflight_manifest_sha256": asset.get("preflight_manifest_sha256", file_sha256(args.asset_manifest)),
        "source_license": asset["license"],
        "runtime": {
            "device": "cuda:0",
            "precision": "float32",
            "batch_size": batch_size,
            "determinism_policy": "ordered_sample_ids_frozen_processor_eval_inference_mode",
            "package_versions": packages,
        },
        "protocol_checks": {"repeated_batching": batching_check},
        "claim_allowed": False,
    }
    atomic_write_json(sidecar, out / "sidecar.json")
    atomic_write_json(
        {
            "status_code": "FEATURE_SHARD_COMPLETE",
            "passed": True,
            "extractor_id": args.extractor_id,
            "shard_id": args.shard_id,
            "configuration_hash": config["configuration_hash"],
            "claim_allowed": False,
        },
        out / "status.json",
    )
    atomic_write_json(
        {**hardware, "rows": len(sample_ids), "dimension": int(matrix.shape[1]), "preprocessing_verified": True},
        out / "worker_status.json",
    )
    completion = {
        **completion_identity_fields(
            "feature",
            config_schema_version=str(config.get("schema_version", "certgen.cvpr.feature_config.v1")),
            output_schema_version=str(config["output_schema_version"]),
        ),
        "status": "success",
        "configuration_hash": config["configuration_hash"],
        "input_manifest_hash": file_sha256(args.image_manifest),
        "asset_manifest_hash": file_sha256(args.asset_manifest),
        "outputs": {
            "features.npz": file_sha256(out / "features.npz"),
            "sidecar.json": file_sha256(out / "sidecar.json"),
            "status.json": file_sha256(out / "status.json"),
        },
        "claim_allowed": False,
    }
    atomic_write_json(completion, out / "worker_completion.json")
    adapter.unload()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
