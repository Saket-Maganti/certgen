"""Sharding-aware feature extraction entrypoint for Kaggle runbooks.

This module is intentionally thin: it validates shard arguments, writes a
shard manifest, then delegates to the guarded extraction CLI. Real model loading
still requires ``--execute`` and optional vision dependencies. Without
``--execute`` it emits a dry-run plan and performs no GPU work.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from certgen.cli.run_feature_extraction import run_feature_extraction
from certgen.core.hashing import file_sha256
from certgen.core.io import read_json, write_json
from certgen.features.extractors.base import read_input_manifest


def _select_shard(rows: list[dict[str, Any]], shard_id: int, num_shards: int) -> list[dict[str, Any]]:
    if num_shards <= 0:
        raise ValueError("num_shards must be positive")
    if shard_id < 0 or shard_id >= num_shards:
        raise ValueError("shard_id must be in [0, num_shards)")
    return [row for index, row in enumerate(rows) if index % num_shards == shard_id]


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def run_sharded_extraction(
    *,
    input_manifest: str,
    extractor: str,
    out_dir: str,
    device: str,
    batch_size: int,
    preprocessing_lock: str,
    provenance_ledger: str | None,
    shard_id: int,
    num_shards: int,
    execute: bool,
    resume: bool,
    force: bool,
    json_out: str | None,
) -> dict[str, Any]:
    rows = read_input_manifest(input_manifest)
    shard_rows = _select_shard(rows, shard_id, num_shards)
    shard_dir = Path(out_dir) / f"shard-{shard_id:03d}-of-{num_shards:03d}"
    feature_path = shard_dir / f"{extractor}_features.npz"
    sidecar_path = shard_dir / f"{extractor}_features.json"
    shard_manifest = shard_dir / "input_manifest.shard.jsonl"
    _write_jsonl(shard_rows, shard_manifest)
    if feature_path.exists() and not (resume or force):
        raise FileExistsError(f"output exists and neither --resume nor --force was set: {feature_path}")
    if resume and not force and (feature_path.exists() or sidecar_path.exists()):
        if not feature_path.is_file() or not sidecar_path.is_file():
            raise RuntimeError("partial feature shard rejected; quarantine and rerun the shard")
        sidecar = read_json(sidecar_path)
        with np.load(feature_path, allow_pickle=False) as loaded:
            features = np.asarray(loaded["features"])
            sample_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
        expected_ids = [str(row["sample_id"]) for row in shard_rows]
        expected_source = file_sha256(input_manifest)
        expected_preprocessing = file_sha256(preprocessing_lock)
        if (
            sidecar.get("extractor") != extractor
            or sidecar.get("sample_ids") != expected_ids
            or sample_ids != expected_ids
            or features.ndim != 2
            or features.shape[0] != len(expected_ids)
            or not np.isfinite(features).all()
            or sidecar.get("hash") != file_sha256(feature_path)
            or sidecar.get("source_manifest_sha256") != expected_source
            or sidecar.get("preprocessing_lock_sha256") != expected_preprocessing
            or int(sidecar.get("shard_id", -1)) != shard_id
            or int(sidecar.get("num_shards", -1)) != num_shards
        ):
            raise RuntimeError("stale or corrupt feature shard rejected; quarantine and rerun the shard")
        return {
            "extractor": extractor,
            "feature_path": str(feature_path),
            "sidecar_path": str(sidecar_path),
            "num_items": len(expected_ids),
            "feature_dim": int(features.shape[1]),
            "shard_id": shard_id,
            "num_shards": num_shards,
            "shard_manifest": str(shard_manifest),
            "source_manifest_sha256": expected_source,
            "preprocessing_lock_sha256": expected_preprocessing,
            "provenance_ledger_sha256": file_sha256(provenance_ledger) if provenance_ledger else None,
            "resumed": True,
            "claim_allowed": False,
        }
    result = run_feature_extraction(
        input_manifest=str(shard_manifest),
        extractor=extractor,
        out_dir=str(shard_dir),
        device=device,
        batch_size=batch_size,
        preprocessing_lock=preprocessing_lock,
        execute=execute,
        json_out=None,
    )
    result.update(
        {
            "shard_id": shard_id,
            "num_shards": num_shards,
            "shard_manifest": str(shard_manifest),
            "source_manifest_sha256": file_sha256(input_manifest),
            "preprocessing_lock_sha256": file_sha256(preprocessing_lock),
            "provenance_ledger_sha256": file_sha256(provenance_ledger) if provenance_ledger else None,
            "claim_allowed": False,
        }
    )
    if execute and sidecar_path.exists():
        sidecar = read_json(sidecar_path)
        with np.load(feature_path, allow_pickle=False) as loaded:
            features = np.asarray(loaded["features"])
        ordered_ids = [str(row["sample_id"]) for row in shard_rows]
        np.savez_compressed(feature_path, features=features, sample_ids=np.asarray(ordered_ids))
        feature_hash = file_sha256(feature_path)
        sidecar.update(
            {
                "sample_ids": ordered_ids,
                "hash": feature_hash,
                "source_manifest_sha256": result["source_manifest_sha256"],
                "preprocessing_lock_sha256": result["preprocessing_lock_sha256"],
                "provenance_ledger_sha256": result["provenance_ledger_sha256"],
                "shard_id": shard_id,
                "num_shards": num_shards,
                "claim_allowed": False,
            }
        )
        write_json(sidecar, sidecar_path)
        result["hash"] = feature_hash
    if json_out:
        write_json(result, json_out)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run sharded CertGen feature extraction.")
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--provenance-ledger")
    parser.add_argument("--preprocessing-lock", required=True)
    parser.add_argument("--extractor", required=True, choices=["inception_v3_pool3", "clip_vit", "dinov2"])
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--shard-id", type=int, required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    parser.add_argument("--json-out")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_sharded_extraction(
            input_manifest=args.input_manifest,
            extractor=args.extractor,
            out_dir=args.out_dir,
            device=args.device,
            batch_size=args.batch_size,
            preprocessing_lock=args.preprocessing_lock,
            provenance_ledger=args.provenance_ledger,
            shard_id=args.shard_id,
            num_shards=args.num_shards,
            execute=args.execute,
            resume=args.resume,
            force=args.force,
            json_out=args.json_out,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    mode = "executed" if args.execute else "planned"
    print(f"{mode} shard {args.shard_id}/{args.num_shards}: {result.get('item_count', result.get('num_items', 0))} items")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
