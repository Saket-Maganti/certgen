"""CPU-only generation-to-feature scientific-payload closure rehearsal."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from certgen.icml2027.common import stable_hash, write_json
from certgen.icml2027.dependency_lifecycle import ensure_dependency_lifecycle, load_dependency_profile
from certgen.icml2027.execution_contract import build_generator_seed_manifest
from certgen.icml2027.notebook_runtime import run_authenticated_lane
from certgen.icml2027.payload import (
    build_copy_forward,
    build_multipart_payload,
    import_multipart_payload,
    validate_multipart_payload,
)
from certgen.icml2027.production_mmd import evaluate_production_contributions
from certgen.metrics.streams import mmd_difference_stream


def _png(seed: int, model_offset: int) -> bytes:
    rng = np.random.default_rng(seed)
    values = rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8)
    values[:, :, model_offset % 3] = (values[:, :, model_offset % 3].astype(np.uint16) + 17) % 256
    buffer = io.BytesIO()
    Image.fromarray(values.astype(np.uint8), mode="RGB").save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def _npz_bytes(features: np.ndarray, sample_ids: list[str]) -> bytes:
    arrays: dict[str, bytes] = {}
    for name, value in {
        "features.npy": features,
        "sample_ids.npy": np.asarray(sample_ids),
    }.items():
        buffer = io.BytesIO()
        np.save(buffer, value, allow_pickle=False)
        arrays[name] = buffer.getvalue()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(arrays.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return output.getvalue()


def _fixture_identity() -> dict[str, Any]:
    return {
        "input_package_sha256": "1" * 64,
        "study_id": "icml2027_cifar_confirmatory_10k_v2",
        "study_hash": "0b77851744d8c6a506cc8530f7fc99a92aa0fefa198c1b64711e1924d944c176",
        "configuration_sha256": "7d543ddd077edeea20bf29d322916a8d0f531ff05787cb779dc2a35506e85e2d",
        "worker_spec_sha256": "2" * 64,
        "source_tree_sha256": "3" * 64,
        "dependency_lock_sha256": "4" * 64,
        "model_revisions": {"fixture_model_a": "fixture-revision-a", "fixture_model_b": "fixture-revision-b"},
        "extractor_revisions": {"fixture_inception": "fixture-v1", "fixture_clip": "fixture-v1"},
        "preprocessing_hashes": {"fixture_inception": "5" * 64, "fixture_clip": "6" * 64},
        "reference_plan_sha256": "f2ae231aa67b0f3b29995451ae56f7fa0a01b0e2410664022dd024a3cb47804e",
        "seed_manifest_sha256": "7" * 64,
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }


def _dependency_fixture(root: Path, profile_path: Path) -> dict[str, Any]:
    profile = load_dependency_profile("cifar_10k_generation", profile_path)
    exact = {str(row["distribution"]): str(row["version"]) for row in profile["lock"]}
    reports = root / "dependency"
    compatible = ensure_dependency_lifecycle(
        lane="cifar_10k_generation",
        input_zip_sha256="8" * 64,
        source_tree_sha256="9" * 64,
        profile_path=profile_path,
        marker_path=reports / "compatible.marker.json",
        report_path=reports / "compatible.report.json",
        mode="USE_PREINSTALLED_VALIDATED",
        installed_versions_override=exact,
        verify_hook=lambda _: {"pip_check": "PASS", "imports": ["fixture"], "claim_allowed": False},
        python_version="3.11.fixture",
        platform_id="fixture-platform",
    )
    install_calls: list[str] = []
    installed = ensure_dependency_lifecycle(
        lane="cifar_10k_generation",
        input_zip_sha256="a" * 64,
        source_tree_sha256="b" * 64,
        profile_path=profile_path,
        marker_path=reports / "install.marker.json",
        report_path=reports / "install.report.json",
        mode="PRIVATE_WHEELHOUSE_OFFLINE",
        wheelhouse=reports,
        installed_versions_override={},
        install_hook=lambda _profile, mode, _wheelhouse: install_calls.append(mode),
        verify_hook=lambda _: {"pip_check": "PASS", "imports": ["fixture"], "claim_allowed": False},
        python_version="3.11.fixture",
        platform_id="fixture-platform",
    )
    second = ensure_dependency_lifecycle(
        lane="cifar_10k_generation",
        input_zip_sha256="a" * 64,
        source_tree_sha256="b" * 64,
        profile_path=profile_path,
        marker_path=reports / "install.marker.json",
        report_path=reports / "install.second.report.json",
        mode="PRIVATE_WHEELHOUSE_OFFLINE",
        wheelhouse=reports,
        installed_versions_override=exact,
        verify_hook=lambda _: {"pip_check": "PASS", "imports": ["fixture"], "claim_allowed": False},
        python_version="3.11.fixture",
        platform_id="fixture-platform",
    )
    return {
        "passed": bool(
            compatible["passed"]
            and installed["restart_required"]
            and second["second_pass_identity_verified"]
            and not second["restart_required"]
            and install_calls == ["PRIVATE_WHEELHOUSE_OFFLINE"]
        ),
        "compatible": compatible,
        "install": installed,
        "second_pass": second,
        "claim_allowed": False,
    }


def run_full_fixture_rehearsal(out_dir: str | Path, *, repo_root: str | Path = ".") -> dict[str, Any]:
    """Exercise actual image/feature bytes, copy-forward, import, and the production MMD path."""

    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    identity = _fixture_identity()
    seed_manifest = build_generator_seed_manifest(count_per_model=100)
    fixture_models = ["fixture_model_a", "fixture_model_b"]
    source_models = ["google_ddpm_cifar10_candidate", "frank_ddpm_ema_cifar10_candidate"]
    generation_parts: list[dict[str, bytes]] = []
    generation_records: list[dict[str, Any]] = []
    image_by_sample: dict[str, bytes] = {}
    sample_ids_by_model: dict[str, list[str]] = {}
    seed_rows = seed_manifest["records"]
    for model_offset, (fixture_model, source_model) in enumerate(zip(fixture_models, source_models, strict=True)):
        rows = [row for row in seed_rows if row["model_id"] == source_model]
        sample_ids_by_model[fixture_model] = [str(row["sample_id"]) for row in rows]
        for shard_id in range(2):
            part: dict[str, bytes] = {}
            manifest_rows: list[dict[str, Any]] = []
            for row in rows[shard_id * 50 : (shard_id + 1) * 50]:
                sample_id = str(row["sample_id"])
                data = _png(int(row["generator_seed"]), model_offset)
                image_path = f"images/{fixture_model}/{sample_id}.png"
                part[image_path] = data
                image_by_sample[sample_id] = data
                record = {
                    "sample_id": sample_id,
                    "sample_index": int(row["sample_index"]),
                    "model_id": fixture_model,
                    "checkpoint_id": f"fixture/{fixture_model}",
                    "checkpoint_revision": f"fixture-revision-{chr(97 + model_offset)}",
                    "generator_seed": int(row["generator_seed"]),
                    "image_path": image_path,
                    "image_sha256": hashlib.sha256(data).hexdigest(),
                    "shard_id": shard_id,
                    "claim_allowed": False,
                }
                generation_records.append(record)
                manifest_rows.append(record)
            part[f"manifests/{fixture_model}.shard{shard_id}.jsonl"] = b"".join(
                (json.dumps(row, sort_keys=True) + "\n").encode() for row in manifest_rows
            )
            generation_parts.append(part)
    generation = build_multipart_payload(
        lane="cifar_10k_generation",
        payload_type="generation",
        parts=generation_parts,
        records=generation_records,
        identity=identity,
        out_dir=target / "generation",
        basename="generation_payload",
    )
    generation_validation = validate_multipart_payload(generation["index_path"], expected_type="generation")
    copy_forward = build_copy_forward(
        generation["index_path"], target / "generation" / "generation_payload_index.json"
    )

    feature_parts: list[dict[str, bytes]] = []
    feature_records: list[dict[str, Any]] = []
    merged: dict[tuple[str, str], list[np.ndarray]] = {}
    extractor_dimensions = {"fixture_inception": 16, "fixture_clip": 24}
    for extractor_index, (extractor, dimension) in enumerate(extractor_dimensions.items()):
        for fixture_model in fixture_models:
            ids = sample_ids_by_model[fixture_model]
            for shard_id in range(2):
                shard_ids = ids[shard_id * 50 : (shard_id + 1) * 50]
                rows = []
                for sample_id in shard_ids:
                    digest_seed = int.from_bytes(hashlib.sha256(image_by_sample[sample_id]).digest()[:8], "big")
                    rng = np.random.default_rng(digest_seed + extractor_index)
                    rows.append(rng.normal(size=dimension).astype(np.float32))
                features = np.stack(rows)
                norms = np.linalg.norm(features, axis=1, keepdims=True)
                features = (features / np.maximum(norms, np.float32(1e-12))).astype(np.float32)
                merged.setdefault((extractor, fixture_model), []).append(features)
                feature_path = f"features/{extractor}/{fixture_model}/shard{shard_id}.npz"
                sidecar_path = f"sidecars/{extractor}/{fixture_model}/shard{shard_id}.json"
                preprocessing = identity["preprocessing_hashes"][extractor]
                sidecar = {
                    "sample_ids": shard_ids,
                    "extractor_id": extractor,
                    "extractor_revision": "fixture-v1",
                    "preprocessing_sha256": preprocessing,
                    "dimension": dimension,
                    "dtype": "float32",
                    "claim_allowed": False,
                }
                feature_parts.append(
                    {
                        feature_path: _npz_bytes(features, shard_ids),
                        sidecar_path: json.dumps(sidecar, sort_keys=True, separators=(",", ":")).encode(),
                    }
                )
                feature_records.append(
                    {
                        "extractor_id": extractor,
                        "extractor_revision": "fixture-v1",
                        "preprocessing_sha256": preprocessing,
                        "source_role": fixture_model,
                        "source_manifest_sha256": generation["global_payload_manifest_sha256"],
                        "feature_path": feature_path,
                        "sidecar_path": sidecar_path,
                        "dimension": dimension,
                        "dtype": "float32",
                        "row_count": len(shard_ids),
                        "source_sample_ids_sha256": stable_hash(shard_ids),
                        "shard_id": shard_id,
                        "claim_allowed": False,
                    }
                )
    feature_identity = {**identity, "generation_payload_index_sha256": generation["payload_index_sha256"]}
    feature_payload = build_multipart_payload(
        lane="cifar_10k_features",
        payload_type="features",
        parts=feature_parts,
        records=feature_records,
        identity=feature_identity,
        out_dir=target / "features",
        basename="feature_payload",
    )
    feature_validation = validate_multipart_payload(feature_payload["index_path"], expected_type="features")
    feature_copy_forward = build_copy_forward(
        feature_payload["index_path"], target / "features" / "feature_payload_index.json"
    )
    imported = import_multipart_payload(feature_payload["index_path"], target / "imported_features")

    a = np.concatenate(merged[("fixture_inception", "fixture_model_a")])
    b = np.concatenate(merged[("fixture_inception", "fixture_model_b")])
    reference = np.roll(a, 1, axis=0)
    stream = mmd_difference_stream(
        a,
        b,
        reference,
        {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
        seed=20_270_812,
        evidence_status="synthetic_validation_only",
        comparison_id="full_closure_fixture",
    )
    certificate = evaluate_production_contributions(stream.values, alpha=0.025)
    certificate_summary = {
        "decision": certificate["decision"],
        "stopping_time": certificate["stopping_time"],
        "mean": certificate["mean"],
        "lower": certificate["lower"],
        "upper": certificate["upper"],
        "method_label": certificate["method_label"],
        "theory_status": certificate["theory_status"],
        "synthetic_validation_only": True,
        "claim_allowed": False,
    }
    write_json(target / "production_mmd_certificate_fixture.json", certificate_summary)
    dependency = _dependency_fixture(
        target, Path(repo_root) / "registry/icml2027/dependency_profiles.json"
    )
    subprocess_fixture = run_authenticated_lane(
        "cifar_10k_generation",
        target / "authenticated_input_fixture",
        target / "worker_subprocess_fixture",
        fixture_mode=True,
        fixture_shards=4,
    )
    summary = {
        "schema_version": "certgen.icml2027.full_generation_feature_rehearsal.v1",
        "passed": bool(
            generation_validation["passed"]
            and feature_validation["passed"]
            and imported["validation"]["passed"]
            and dependency["passed"]
            and subprocess_fixture["result"]["passed"]
        ),
        "fake_models": 2,
        "images_per_model": 100,
        "generation_shards_per_model": 2,
        "fixture_extractors": 2,
        "feature_shards_per_extractor_model": 2,
        "generation_validation": generation_validation,
        "generation_copy_forward_sha256": copy_forward["copy_forward_sha256"],
        "feature_validation": feature_validation,
        "feature_copy_forward_sha256": feature_copy_forward["copy_forward_sha256"],
        "feature_import": imported,
        "production_mmd_certificate": certificate_summary,
        "dependency_lifecycle": dependency,
        "worker_subprocesses": 4,
        "real_gpu_evidence_exists": False,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    summary["rehearsal_sha256"] = stable_hash(summary)
    write_json(target / "FULL_REHEARSAL_SUMMARY.json", summary)
    return summary
