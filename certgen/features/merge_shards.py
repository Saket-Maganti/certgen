"""Merge sharded feature caches deterministically by sample id."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import read_json, write_json


def merge_feature_shards(*, shard_dirs: list[str], extractor: str, out_npz: str, out_sidecar: str, force: bool = False) -> dict:
    out_npz_path = Path(out_npz)
    out_sidecar_path = Path(out_sidecar)
    if (out_npz_path.exists() or out_sidecar_path.exists()) and not force:
        raise FileExistsError("merged output exists; pass --force to overwrite")
    rows = []
    for shard_dir in shard_dirs:
        root = Path(shard_dir)
        npz_path = root / f"{extractor}_features.npz"
        sidecar_path = root / f"{extractor}_features.json"
        if not npz_path.exists() or not sidecar_path.exists():
            raise FileNotFoundError(f"missing shard cache: {npz_path} or {sidecar_path}")
        sidecar = read_json(sidecar_path)
        with np.load(npz_path, allow_pickle=False) as loaded:
            features = np.asarray(loaded["features"])
        sample_ids = [str(value) for value in sidecar.get("sample_ids", [])]
        if len(sample_ids) != features.shape[0]:
            raise ValueError(f"sample_ids length mismatch for {shard_dir}")
        for sample_id, feature in zip(sample_ids, features):
            rows.append((sample_id, feature, str(npz_path), sidecar))
    seen = set()
    duplicates = []
    for sample_id, *_ in rows:
        if sample_id in seen:
            duplicates.append(sample_id)
        seen.add(sample_id)
    if duplicates:
        raise ValueError(f"duplicate sample ids across shards: {duplicates[:5]}")
    rows.sort(key=lambda item: item[0])
    merged = np.stack([row[1] for row in rows]).astype(np.float32) if rows else np.empty((0, 0), dtype=np.float32)
    sample_ids = np.asarray([row[0] for row in rows])
    out_npz_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz_path, features=merged, sample_ids=sample_ids)
    source_sidecars = [row[3] for row in rows[:1]]
    template = source_sidecars[0] if source_sidecars else {}
    sidecar = {
        "extractor": extractor,
        "feature_extractor": extractor,
        "model_id": template.get("model_id"),
        "model_revision": template.get("model_revision"),
        "weights_id": template.get("weights_id"),
        "weights_url": template.get("weights_url"),
        "dependency_versions": template.get("dependency_versions", {}),
        "feature_dim": int(merged.shape[1]) if merged.ndim == 2 and merged.size else 0,
        "n_samples": int(merged.shape[0]),
        "num_items": int(merged.shape[0]),
        "sample_ids": sample_ids.tolist(),
        "feature_path": str(out_npz_path),
        "features_sha256": file_sha256(out_npz_path),
        "hash": file_sha256(out_npz_path),
        "shard_dirs": shard_dirs,
        "merged_sorted_by": "sample_id",
        "source_sidecar_template": template,
        "preprocessing": template.get("preprocessing", {}),
        "source": template.get("source", {}),
        "hashes": {
            "features_sha256": file_sha256(out_npz_path),
            "source_manifest_sha256": template.get("source_manifest_sha256")
            or (template.get("hashes") or {}).get("source_manifest_sha256"),
            "preprocessing_lock_sha256": template.get("preprocessing_lock_sha256")
            or (template.get("hashes") or {}).get("preprocessing_lock_sha256"),
        },
        "created_by": "certgen.features.merge_shards",
        "evidence_status": "real_features_unvalidated",
        "claim_allowed": False,
    }
    write_json(sidecar, out_sidecar_path)
    return sidecar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge CertGen sharded feature caches.")
    parser.add_argument("--shard-dir", action="append", required=True)
    parser.add_argument("--extractor", required=True)
    parser.add_argument("--out-npz", required=True)
    parser.add_argument("--out-sidecar", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = merge_feature_shards(
            shard_dirs=args.shard_dir,
            extractor=args.extractor,
            out_npz=args.out_npz,
            out_sidecar=args.out_sidecar,
            force=args.force,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Merged {result['n_samples']} samples -> {args.out_npz}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
