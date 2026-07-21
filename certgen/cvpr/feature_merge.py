"""Deterministic local merge of imported CVPR feature shards into cache-v2."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from certgen import __version__
from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.features.cache_v2 import SCHEMA_VERSION, validate_feature_cache_v2
from certgen.features.protocol_checks import independent_shard_merge_check
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry


def _resolve_imported_run(run: str | Path, imported_root: str | Path = "data/imported") -> Path:
    direct = Path(run)
    if direct.is_dir():
        return direct.resolve()
    base = Path(imported_root)
    exact = base / str(run)
    if exact.is_dir():
        return exact.resolve()
    candidates = [path for path in base.glob(f"*{run}*") if path.is_dir()]
    if len(candidates) != 1:
        raise FileNotFoundError(f"expected one imported feature run for {run!s}; found {len(candidates)}")
    return candidates[0].resolve()


def _preprocessing(expected: dict[str, Any]) -> dict[str, Any]:
    return {
        "resize": expected.get("resize_size"),
        "interpolation": expected.get("interpolation"),
        "crop": {"mode": expected.get("crop_mode"), "size": expected.get("crop_size")},
        "color_mode": "rgb",
        "pixel_range": expected.get("pixel_range"),
        "normalization": {"mean": expected.get("mean"), "std": expected.get("std")},
        "feature_normalization": expected.get("feature_normalization"),
    }


def _atomic_npz(path: Path, features: np.ndarray, sample_ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, features=features, sample_ids=np.asarray(sample_ids))
    os.replace(temporary, path)


def merge_feature_run(
    run: str | Path,
    *,
    imported_root: str | Path = "data/imported",
    output_root: str | Path = "data/features/cvpr",
    registry_path: str | Path = "data/artifact_registry.jsonl",
) -> dict[str, Any]:
    source = _resolve_imported_run(run, imported_root)
    run_id = source.name
    destination = Path(output_root) / run_id
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite merged feature run: {destination}")
    sidecar_paths = sorted(source.glob("shards/*/*/sidecar.json"))
    if not sidecar_paths:
        sidecar_paths = sorted(source.glob("shards/*/sidecar.json"))
    if not sidecar_paths:
        raise FileNotFoundError("imported feature run contains no canonical shard sidecars")
    groups: dict[tuple[str, str, str], list[tuple[Path, dict[str, Any]]]] = {}
    for sidecar_path in sidecar_paths:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        if sidecar.get("schema_version") != "certgen.feature_shard.v2":
            raise ValueError(f"unsupported feature shard schema: {sidecar_path}")
        key = (str(sidecar["extractor_id"]), str(sidecar["role"]), str(sidecar["model_id"]))
        groups.setdefault(key, []).append((sidecar_path, sidecar))
    destination.mkdir(parents=True)
    cache_results: list[dict[str, Any]] = []
    merge_rows: list[dict[str, Any]] = []
    try:
        for (extractor_id, role_name, model_id), shards in sorted(groups.items()):
            rows: list[tuple[str, np.ndarray]] = []
            dimension: int | None = None
            preprocessing_hash: str | None = None
            template: dict[str, Any] = {}
            shard_hashes: list[str] = []
            batching_checks: list[dict[str, Any]] = []
            for sidecar_path, sidecar in shards:
                array_path = sidecar_path.with_name("features.npz")
                if not array_path.is_file() or file_sha256(array_path) != sidecar.get("array_sha256"):
                    raise ValueError(f"feature shard hash mismatch: {array_path}")
                if dimension is None:
                    dimension = int(sidecar["dimension"])
                    preprocessing_hash = str(sidecar["preprocessing_hash"])
                    template = sidecar
                if int(sidecar["dimension"]) != dimension or str(sidecar["preprocessing_hash"]) != preprocessing_hash:
                    raise ValueError("feature shards disagree on dimension or preprocessing")
                batching = (sidecar.get("protocol_checks") or {}).get("repeated_batching")
                if not isinstance(batching, dict) or batching.get("passed") is not True:
                    raise ValueError(
                        f"feature shard lacks a passing repeated-batching check: {sidecar_path}"
                    )
                batching_checks.append(batching)
                with np.load(array_path, allow_pickle=False) as loaded:
                    features = np.asarray(loaded["features"])
                    sample_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
                if features.ndim != 2 or features.shape != (len(sample_ids), dimension):
                    raise ValueError(f"feature shard shape mismatch: {array_path}")
                if not np.isfinite(features).all():
                    raise ValueError(f"feature shard contains nonfinite values: {array_path}")
                rows.extend(zip(sample_ids, features, strict=True))
                shard_hashes.append(file_sha256(array_path))
            ids = [sample_id for sample_id, _ in rows]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate feature sample ID in {extractor_id}/{role_name}")
            rows.sort(key=lambda item: item[0])
            sample_ids = [row[0] for row in rows]
            matrix = np.stack([row[1] for row in rows]).astype(np.float32)
            shard_merge_check = independent_shard_merge_check(sample_ids, matrix)
            if not shard_merge_check["passed"]:
                raise ValueError(
                    f"independent shard-merge validation failed: {extractor_id}/{role_name}"
                )
            canonical_role = str(template.get("canonical_role") or (
                "reference" if role_name == "reference" else "model"
            ))
            portable_role = "reference" if canonical_role == "reference" else "model"
            group = destination / extractor_id / role_name
            features_path = group / "features.npz"
            source_manifest = group / "source_manifest.jsonl"
            source_manifest.parent.mkdir(parents=True, exist_ok=True)
            source_manifest.write_text(
                "".join(
                    json.dumps(
                        {
                            "sample_id": sample_id,
                            "role": portable_role,
                            "canonical_role": canonical_role,
                            "model_id": model_id,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                    for sample_id in sample_ids
                ),
                encoding="utf-8",
            )
            _atomic_npz(features_path, matrix, sample_ids)
            expected = dict(template["expected_preprocessing"])
            sidecar = {
                "schema_version": SCHEMA_VERSION,
                "cache_id": stable_hash_json({"run": run_id, "extractor": extractor_id, "role": role_name, "array": file_sha256(features_path)})[:24],
                "role": portable_role,
                "canonical_role": canonical_role,
                "role_id": role_name,
                "benchmark": {
                    "dataset_id": "cifar10",
                    "split": "test" if portable_role == "reference" else "generated",
                    "source_manifest_path": source_manifest.relative_to(destination).as_posix(),
                    "source_manifest_sha256": file_sha256(source_manifest),
                },
                "producer": {
                    "model_or_generator_id": model_id,
                    "checkpoint_or_revision": template.get("producer_revision") or "imported_preflight_validated_revision",
                },
                "extractor": {
                    "name": extractor_id,
                    "resolved_model_id": template["resolved_model_id"],
                    "resolved_revision": template["resolved_revision"],
                    "package_versions": template.get("runtime", {}).get("package_versions", {}),
                    "output_layer": str(
                        (template.get("output_definition") or {}).get(
                            "feature_definition", "explicit_feature_definition_missing"
                        )
                    ),
                    "output_definition": template.get("output_definition"),
                    "feature_dim": int(dimension or 0),
                },
                "preprocessing": _preprocessing(expected),
                "array": {
                    "path": features_path.relative_to(destination).as_posix(),
                    "sha256": file_sha256(features_path),
                    "dtype": str(matrix.dtype),
                    "shape": list(matrix.shape),
                    "features_key": "features",
                    "sample_ids_key": "sample_ids",
                    "ordered_sample_ids_sha256": stable_hash_json(sample_ids),
                },
                "shard": {
                    "shard_id": "merged",
                    "num_shards": len(shards),
                    "selection_policy": "stable_sample_id_sorted_role_preserving",
                    "input_shard_manifest_sha256": stable_hash_json(shard_hashes),
                },
                "runtime": {
                    "device": template.get("runtime", {}).get("device", "cuda:0"),
                    "precision": "float32",
                    "batch_size": template.get("runtime", {}).get("batch_size", 1),
                    "determinism_policy": "stable_sample_id_sorted_atomic_npz",
                    "created_by": "certgen.cvpr.feature_merge.merge_feature_run",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "certgen_version": __version__,
                },
                "source": {"license_status": template.get("source_license", "preflight_approved")},
                "image_manifest": {
                    "schema_version": template.get(
                        "image_manifest_schema_version", "certgen.cvpr.image_manifest.v1"
                    ),
                    "source_manifest_hash": template.get("source_manifest_hash"),
                    "role_id": role_name,
                    "canonical_role": canonical_role,
                },
                "protocol_checks": {
                    "repeated_batching": batching_checks,
                    "independent_shard_merge": shard_merge_check,
                },
                "evidence": {"status": "real_features_unvalidated", "claim_allowed": False},
                "claim_allowed": False,
            }
            sidecar_path = group / "sidecar.json"
            atomic_write_json(sidecar, sidecar_path)
            validation = validate_feature_cache_v2(features_path=features_path, sidecar_path=sidecar_path, artifact_root=destination)
            if not validation["passed"]:
                raise ValueError("merged cache-v2 validation failed: " + "; ".join(validation["errors"]))
            cache_results.append(validation)
            merge_rows.append({"feature_space": extractor_id, "role": role_name, "model_id": model_id, "rows": len(sample_ids), "features_sha256": file_sha256(features_path), "sidecar_sha256": file_sha256(sidecar_path)})
            append_artifact_entry(
                build_artifact_entry(path=features_path, artifact_type="cvpr_feature_cache_v2", stage="feature_merge", run_id=run_id, source=str(source), validation_status="cache_v2_validated", evidence_class="PILOT_ARTIFACT", notes="Merged imported shards; still not paper evidence."),
                registry_path,
            )
        manifest = {
            "schema_version": "certgen.cvpr.feature_merge.v1",
            "run_id": run_id,
            "source_import": str(source),
            "groups": merge_rows,
            "claim_allowed": False,
        }
        atomic_write_json(manifest, destination / "merge_manifest.json")
        status = {
            "status_code": "FEATURE_CACHE_V2_MERGE_COMPLETE",
            "passed": True,
            "run_id": run_id,
            "groups": len(merge_rows),
            "merge_manifest_sha256": file_sha256(destination / "merge_manifest.json"),
            "claim_allowed": False,
        }
        atomic_write_json(status, destination / "status.json")
        return {**status, "output_dir": str(destination), "validations": cache_results}
    except Exception:
        # A failed partial merge is never reusable as a complete cache.
        if destination.exists():
            quarantine = destination.with_name(destination.name + "__FAILED_PARTIAL")
            if quarantine.exists():
                raise
            os.replace(destination, quarantine)
        raise
