"""Split merged feature caches into role-specific arrays.

Kaggle feature extraction writes one merged cache per extractor. The CPU
certificate path needs role-specific arrays, so this command joins feature
sample IDs back to the sample manifest and writes one cache per role.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import read_json, write_json


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def split_feature_cache_by_role(
    *,
    features_npz: str | Path,
    sidecar: str | Path,
    sample_manifest: str | Path,
    extractor_label: str,
    out_dir: str | Path,
    allowed_roles: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    features_npz = Path(features_npz)
    sidecar_path = Path(sidecar)
    out_dir = Path(out_dir)
    source_sidecar = read_json(sidecar_path)
    with np.load(features_npz, allow_pickle=False) as loaded:
        features = np.asarray(loaded["features"], dtype=np.float32)
        if "sample_ids" in loaded:
            sample_ids = [str(item) for item in loaded["sample_ids"]]
        else:
            sample_ids = [str(item) for item in source_sidecar.get("sample_ids", [])]
    if len(sample_ids) != int(features.shape[0]):
        raise ValueError("sample_ids length does not match feature rows")

    manifest_by_id: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(sample_manifest):
        sample_id = str(row.get("sample_id", ""))
        if sample_id:
            manifest_by_id[sample_id] = row
    missing_manifest = [sample_id for sample_id in sample_ids if sample_id not in manifest_by_id]
    if missing_manifest:
        raise ValueError(f"{len(missing_manifest)} feature sample IDs are missing from the sample manifest")

    allowed = set(allowed_roles or [])
    grouped: dict[str, list[tuple[str, np.ndarray]]] = {}
    for sample_id, vector in zip(sample_ids, features):
        role = str(manifest_by_id[sample_id].get("role", ""))
        if not role:
            raise ValueError(f"sample has no role in manifest: {sample_id}")
        if allowed and role not in allowed:
            continue
        grouped.setdefault(role, []).append((sample_id, vector))
    if not grouped:
        raise ValueError("no feature rows matched the requested roles")

    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, dict[str, Any]] = {}
    for role, rows in sorted(grouped.items()):
        rows.sort(key=lambda item: item[0])
        out_npz = out_dir / f"{role}_{extractor_label}.npz"
        out_sidecar = out_dir / f"{role}_{extractor_label}.sidecar.json"
        if (out_npz.exists() or out_sidecar.exists()) and not force:
            raise FileExistsError(f"split cache exists for role {role}; pass --force to overwrite")
        role_sample_ids = np.asarray([sample_id for sample_id, _ in rows])
        role_features = np.stack([vector for _, vector in rows]).astype(np.float32)
        np.savez_compressed(out_npz, features=role_features, sample_ids=role_sample_ids)
        role_sidecar = {
            "extractor": source_sidecar.get("extractor") or source_sidecar.get("feature_extractor") or extractor_label,
            "feature_extractor": source_sidecar.get("feature_extractor") or source_sidecar.get("extractor") or extractor_label,
            "model_id": source_sidecar.get("model_id"),
            "model_revision": source_sidecar.get("model_revision"),
            "weights_id": source_sidecar.get("weights_id"),
            "weights_url": source_sidecar.get("weights_url"),
            "dependency_versions": source_sidecar.get("dependency_versions", {}),
            "role": role,
            "feature_dim": int(role_features.shape[1]),
            "n_samples": int(role_features.shape[0]),
            "num_items": int(role_features.shape[0]),
            "sample_ids": role_sample_ids.tolist(),
            "feature_path": str(out_npz),
            "features_sha256": file_sha256(out_npz),
            "hash": file_sha256(out_npz),
            "preprocessing": source_sidecar.get("preprocessing", {}),
            "source": source_sidecar.get("source", {}),
            "hashes": {
                "features_sha256": file_sha256(out_npz),
                "source_manifest_sha256": source_sidecar.get("source_manifest_sha256")
                or (source_sidecar.get("hashes") or {}).get("source_manifest_sha256"),
                "preprocessing_lock_sha256": source_sidecar.get("preprocessing_lock_sha256")
                or (source_sidecar.get("hashes") or {}).get("preprocessing_lock_sha256"),
            },
            "created_by": "certgen.features.split_by_role",
            "source_merged_feature_cache": str(features_npz),
            "source_merged_sidecar": str(sidecar_path),
            "source_manifest": str(sample_manifest),
            "evidence_status": "real_features_unvalidated",
            "claim_allowed": False,
        }
        write_json(role_sidecar, out_sidecar)
        outputs[role] = {
            "features_npz": str(out_npz),
            "sidecar": str(out_sidecar),
            "n_samples": int(role_features.shape[0]),
            "claim_allowed": False,
        }

    return {
        "passed": True,
        "source_features_npz": str(features_npz),
        "source_sidecar": str(sidecar_path),
        "sample_manifest": str(sample_manifest),
        "extractor_label": extractor_label,
        "outputs": outputs,
        "roles": sorted(outputs),
        "evidence_status": "real_features_unvalidated",
        "claim_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split a merged feature cache into role-specific caches.")
    parser.add_argument("--features-npz", required=True)
    parser.add_argument("--sidecar", required=True)
    parser.add_argument("--sample-manifest", required=True)
    parser.add_argument("--extractor-label", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--role", action="append", default=None)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = split_feature_cache_by_role(
            features_npz=args.features_npz,
            sidecar=args.sidecar,
            sample_manifest=args.sample_manifest,
            extractor_label=args.extractor_label,
            out_dir=args.out_dir,
            allowed_roles=args.role,
            force=args.force,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    write_json(summary, args.summary_out)
    print(f"Split roles: {', '.join(summary['roles'])}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
