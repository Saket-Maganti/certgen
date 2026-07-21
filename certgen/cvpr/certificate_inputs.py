"""Immutable, family-complete certificate-input bundles from cache-v2 roles."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.registries import validate_family_record
from certgen.cvpr.study import require_frozen_study
from certgen.features.cache_v2 import validate_feature_cache_v2
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry
from certgen.stats.reference_sampling import validate_reference_draw_plan


SCHEMA_VERSION = "certgen.cvpr.certificate_inputs.v1"


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _family_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_dir():
        path = path / "family.json"
    if not path.is_file():
        raise FileNotFoundError(f"frozen family artifact missing: {path}")
    return path


def _role(model_id: str) -> str:
    controls = {
        "reference_split_a",
        "reference_split_b",
        "reference_clean",
        "reference_severe_corruption",
    }
    if model_id == "reference":
        return "reference"
    return f"control__{model_id}" if model_id in controls else f"model__{model_id}"


def _frozen_preprocessing(expected: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "resize": expected.get("resize_size"),
        "interpolation": expected.get("interpolation"),
        "crop": {"mode": expected.get("crop_mode"), "size": expected.get("crop_size")},
        "color_mode": "rgb",
        "pixel_range": expected.get("pixel_range"),
        "normalization": {"mean": expected.get("mean"), "std": expected.get("std")},
        "feature_normalization": expected.get("feature_normalization"),
    }


def _cache(feature_root: Path, feature_space: str, role_id: str) -> tuple[Path, Path, dict[str, Any]]:
    group = feature_root / feature_space / role_id
    array = group / "features.npz"
    sidecar_path = group / "sidecar.json"
    verdict = validate_feature_cache_v2(
        features_path=array,
        sidecar_path=sidecar_path,
        artifact_root=feature_root,
    )
    if not verdict["passed"]:
        raise ValueError(
            f"cache-v2 role {feature_space}/{role_id} is invalid: " + "; ".join(verdict["errors"])
        )
    return array, sidecar_path, _json(sidecar_path)


def _array(path: Path, budget: int) -> tuple[np.ndarray, list[str]]:
    with np.load(path, allow_pickle=False) as loaded:
        matrix = np.asarray(loaded["features"], dtype=np.float32)
        ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise ValueError(f"cache contains duplicate or missing sample IDs: {path}")
    if len(ids) < budget:
        raise ValueError(f"cache has {len(ids)} rows but frozen hypothesis requires {budget}: {path}")
    return matrix[:budget], ids[:budget]


def _registry_hashes(path: Path) -> set[str]:
    if not path.is_file():
        raise FileNotFoundError(f"artifact registry missing: {path}")
    values: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            digest = row.get("hash", {}).get("value") if isinstance(row.get("hash"), dict) else None
            if isinstance(digest, str):
                values.add(digest)
    return values


def _bundle_dir(root: Path, study_hash: str, family: Mapping[str, Any], hypothesis: Mapping[str, Any]) -> Path:
    same_lane = [
        row
        for row in family["hypotheses"]
        if row["comparison_id"] == hypothesis["comparison_id"]
        and row["feature_space"] == hypothesis["feature_space"]
    ]
    base = root / study_hash / str(family["family_id"]) / str(hypothesis["comparison_id"]) / str(hypothesis["feature_space"])
    if len(same_lane) == 1:
        return base
    return base / str(hypothesis["metric"]) / f"n{hypothesis['sample_budget']}"


def validate_bundle(
    bundle: str | Path,
    *,
    sidecar: str | Path | None = None,
    study_hash: str | None = None,
    family_hash: str | None = None,
) -> dict[str, Any]:
    bundle_path = Path(bundle)
    sidecar_path = Path(sidecar) if sidecar is not None else bundle_path.with_name("sidecar.json")
    errors: list[str] = []
    if not bundle_path.is_file() or not sidecar_path.is_file():
        return {"passed": False, "errors": ["certificate bundle or sidecar missing"], "claim_allowed": False}
    metadata = _json(sidecar_path)
    required = {
        "comparison_id", "family_id", "family_hash", "study_hash", "feature_space", "metric",
        "kernel", "bandwidth", "budget", "model_a", "model_b", "role_manifest_hash",
        "reference_draw_hash", "feature_cache_hashes", "preprocessing_hash", "extractor_hash",
        "alpha_total", "alpha_hypothesis", "configuration_hash", "evidence_class", "claim_allowed",
    }
    errors.extend(f"missing bundle sidecar field: {field}" for field in sorted(required - set(metadata)))
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported certificate-input schema version")
    if metadata.get("claim_allowed") is not False:
        errors.append("certificate inputs must set claim_allowed=false")
    if study_hash is not None and metadata.get("study_hash") != study_hash:
        errors.append("certificate-input study hash mismatch")
    if family_hash is not None and metadata.get("family_hash") != family_hash:
        errors.append("certificate-input family hash mismatch")
    if metadata.get("bundle_sha256") != file_sha256(bundle_path):
        errors.append("certificate-input NPZ hash mismatch")
    configuration_payload = {key: value for key, value in metadata.items() if key not in {"configuration_hash", "bundle_sha256"}}
    if metadata.get("configuration_hash") != stable_hash_json(configuration_payload):
        errors.append("certificate-input configuration hash mismatch")
    try:
        with np.load(bundle_path, allow_pickle=False) as loaded:
            required_arrays = {
                "features_a", "features_b", "features_r", "sample_ids_a", "sample_ids_b",
                "source_ids_r", "source_population_ids", "reference_draw_ids",
            }
            errors.extend(f"missing bundle array: {name}" for name in sorted(required_arrays - set(loaded.files)))
            if not errors:
                arrays = [np.asarray(loaded[name]) for name in ("features_a", "features_b", "features_r")]
                budget = int(metadata["budget"])
                if any(array.ndim != 2 or len(array) != budget for array in arrays):
                    errors.append("feature arrays do not match the frozen budget")
                if not all(np.isfinite(array).all() for array in arrays):
                    errors.append("feature arrays contain nonfinite values")
                for name, expected in (("sample_ids_a", budget), ("sample_ids_b", budget), ("source_ids_r", budget), ("reference_draw_ids", budget)):
                    ids = [str(value) for value in np.asarray(loaded[name]).tolist()]
                    if len(ids) != expected or len(ids) != len(set(ids)) or any(not value for value in ids):
                        errors.append(f"{name} must contain {expected} unique non-empty IDs")
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"certificate-input NPZ invalid: {exc}")
    return {"passed": not errors, "errors": errors, "sidecar": str(sidecar_path), "claim_allowed": False}


def prepare_certificate_inputs(
    *,
    study_path: str | Path,
    family_path: str | Path,
    feature_run: str | Path,
    reference_draw_plan: str | Path,
    out_root: str | Path = "artifacts/cvpr/certificate_inputs",
    registry_path: str | Path = "data/artifact_registry.jsonl",
    dry_run: bool = False,
) -> dict[str, Any]:
    study = require_frozen_study(study_path)
    family_file = _family_path(family_path)
    family = _json(family_file)
    family_verdict = validate_family_record(family, require_frozen=True)
    if not family_verdict["passed"]:
        raise ValueError("family is not frozen/valid: " + "; ".join(family_verdict["errors"]))
    if family.get("study_hash") != study["configuration_hash"]:
        raise ValueError("family and frozen study hashes differ")
    draw_file = Path(reference_draw_plan)
    plan = _json(draw_file)
    # Full validation is performed against the unique source population below when
    # available from the canonical plan metadata; basic self-validation is still mandatory here.
    draw_verdict = validate_reference_draw_plan(plan, min_draws=max(int(row["sample_budget"]) for row in family["hypotheses"]))
    if not draw_verdict["passed"]:
        raise ValueError("reference draw plan invalid: " + "; ".join(draw_verdict["errors"]))
    feature_root = Path(feature_run)
    if not feature_root.is_dir():
        raise FileNotFoundError(f"merged feature run missing: {feature_root}")
    registered = _registry_hashes(Path(registry_path))
    results: list[dict[str, Any]] = []
    for hypothesis in family["hypotheses"]:
        budget = int(hypothesis["sample_budget"])
        feature_space = str(hypothesis["feature_space"])
        roles = (_role(str(hypothesis["model_a"])), _role(str(hypothesis["model_b"])), "reference")
        cache_rows = [_cache(feature_root, feature_space, role) for role in roles]
        frozen_definition = study.get("feature_definitions", {}).get(feature_space)
        if not isinstance(frozen_definition, Mapping):
            raise ValueError(f"feature space is absent from frozen study definitions: {feature_space}")
        expected_preprocessing = frozen_definition.get("expected_preprocessing")
        if not isinstance(expected_preprocessing, Mapping):
            raise ValueError(f"frozen preprocessing declaration missing: {feature_space}")
        for _, _, cache_sidecar in cache_rows:
            extractor = cache_sidecar["extractor"]
            if (
                extractor.get("resolved_model_id") != frozen_definition.get("model_identifier")
                or extractor.get("resolved_revision") != frozen_definition.get("revision")
                or cache_sidecar.get("preprocessing") != _frozen_preprocessing(expected_preprocessing)
            ):
                raise ValueError(f"cache extractor/preprocessing differs from frozen study: {feature_space}")
        cache_hashes = {role: file_sha256(row[0]) for role, row in zip(roles, cache_rows, strict=True)}
        unregistered = sorted(set(cache_hashes.values()) - registered)
        if unregistered:
            raise ValueError("certificate input cache is absent from the artifact registry: " + ", ".join(unregistered))
        preprocessing_hashes = {stable_hash_json(row[2]["preprocessing"]) for row in cache_rows}
        extractor_hashes = {stable_hash_json(row[2]["extractor"]) for row in cache_rows}
        if len(preprocessing_hashes) != 1:
            raise ValueError(f"mixed preprocessing in hypothesis {hypothesis['hypothesis_id']}")
        if len(extractor_hashes) != 1:
            raise ValueError(f"mixed extractor revision in hypothesis {hypothesis['hypothesis_id']}")
        arrays = [_array(row[0], budget) for row in cache_rows]
        reference_ids = arrays[2][1]
        expected_draw_ids = [str(row["draw_id"]) for row in plan["draws"][:budget]]
        if reference_ids != expected_draw_ids:
            raise ValueError("reference cache order differs from the frozen draw plan")
        source_population = [str(value) for value in plan.get("source_population_ids", [])]
        if not source_population:
            raise ValueError("canonical reference draw plan omits source_population_ids")
        role_hash = stable_hash_json([row[2]["benchmark"]["source_manifest_sha256"] for row in cache_rows])
        metadata: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "hypothesis_id": hypothesis["hypothesis_id"],
            "comparison_id": hypothesis["comparison_id"],
            "family_id": family["family_id"],
            "family_hash": family["configuration_hash"],
            "study_hash": study["configuration_hash"],
            "feature_space": feature_space,
            "metric": hypothesis["metric"],
            "kernel": family["kernel"],
            "bandwidth": family["bandwidth"],
            "budget": budget,
            "model_a": hypothesis["model_a"],
            "model_b": hypothesis["model_b"],
            "role_ids": list(roles),
            "role_manifest_hash": role_hash,
            "reference_draw_hash": plan["configuration_hash"],
            "feature_cache_hashes": cache_hashes,
            "preprocessing_hash": next(iter(preprocessing_hashes)),
            "extractor_hash": next(iter(extractor_hashes)),
            "frozen_feature_definition_hash": stable_hash_json(frozen_definition),
            "alpha_total": family["alpha_total"],
            "alpha_hypothesis": family["alpha_per_hypothesis"],
            "source_population_hash": plan["source_ids_sha256"],
            "evidence_class": "pilot_input_only",
            "claim_allowed": False,
        }
        metadata["configuration_hash"] = stable_hash_json(metadata)
        destination = _bundle_dir(Path(out_root), study["configuration_hash"], family, hypothesis)
        bundle_path = destination / "certificate_inputs.npz"
        if dry_run:
            results.append({"hypothesis_id": hypothesis["hypothesis_id"], "path": str(bundle_path), "configuration_hash": metadata["configuration_hash"]})
            continue
        if destination.exists():
            verdict = validate_bundle(bundle_path, study_hash=study["configuration_hash"], family_hash=family["configuration_hash"])
            existing = _json(destination / "sidecar.json") if (destination / "sidecar.json").is_file() else {}
            if verdict["passed"] and existing.get("configuration_hash") == metadata["configuration_hash"]:
                results.append({"hypothesis_id": hypothesis["hypothesis_id"], "path": str(bundle_path), "configuration_hash": metadata["configuration_hash"]})
                continue
            raise FileExistsError(f"existing certificate-input bundle is not an identical valid build: {destination}")
        destination.mkdir(parents=True)
        temporary = bundle_path.with_name(f".{bundle_path.name}.tmp")
        with temporary.open("wb") as handle:
            np.savez_compressed(
                handle,
                features_a=arrays[0][0], features_b=arrays[1][0], features_r=arrays[2][0],
                sample_ids_a=np.asarray(arrays[0][1]), sample_ids_b=np.asarray(arrays[1][1]),
                source_ids_r=np.asarray(reference_ids), source_population_ids=np.asarray(source_population),
                reference_draw_ids=np.asarray(expected_draw_ids),
            )
        os.replace(temporary, bundle_path)
        metadata["bundle_sha256"] = file_sha256(bundle_path)
        atomic_write_json(metadata, destination / "sidecar.json")
        verdict = validate_bundle(bundle_path, study_hash=study["configuration_hash"], family_hash=family["configuration_hash"])
        atomic_write_json(verdict, destination / "validation.json")
        if not verdict["passed"]:
            raise ValueError("generated certificate-input bundle invalid: " + "; ".join(verdict["errors"]))
        entry = build_artifact_entry(
            path=bundle_path, artifact_type="cvpr_certificate_input_bundle", stage="certificate_inputs",
            run_id=str(hypothesis["hypothesis_id"]), source=str(feature_root),
            validation_status="certificate_input_validated", evidence_class="pilot_input_only",
            notes="Immutable family-bound certificate input; claim_allowed=false.",
        )
        append_artifact_entry(entry, registry_path)
        results.append({"hypothesis_id": hypothesis["hypothesis_id"], "path": str(bundle_path), "configuration_hash": metadata["configuration_hash"]})
    manifest = {
        "schema_version": "certgen.cvpr.certificate_input_manifest.v1",
        "status": "CERTIFICATE_INPUTS_READY",
        "study_hash": study["configuration_hash"],
        "family_id": family["family_id"],
        "family_hash": family["configuration_hash"],
        "bundles": results,
        "expected_hypotheses": len(family["hypotheses"]),
        "dry_run": dry_run,
        "claim_allowed": False,
    }
    if not dry_run:
        manifest_path = Path(out_root) / study["configuration_hash"] / str(family["family_id"]) / "bundle_manifest.json"
        atomic_write_json(manifest, manifest_path)
    return manifest


def validate_certificate_inputs(
    *,
    study_path: str | Path,
    family_path: str | Path,
    inputs_root: str | Path = "artifacts/cvpr/certificate_inputs",
    out_path: str | Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    study = require_frozen_study(study_path)
    family = _json(_family_path(family_path))
    errors: list[str] = []
    seen: set[str] = set()
    for hypothesis in family.get("hypotheses", []):
        destination = _bundle_dir(Path(inputs_root), study["configuration_hash"], family, hypothesis)
        verdict = validate_bundle(
            destination / "certificate_inputs.npz",
            study_hash=study["configuration_hash"],
            family_hash=family.get("configuration_hash"),
        )
        if not verdict["passed"]:
            errors.extend(f"{hypothesis['hypothesis_id']}: {error}" for error in verdict["errors"])
            continue
        sidecar = _json(destination / "sidecar.json")
        if sidecar.get("hypothesis_id") != hypothesis.get("hypothesis_id"):
            errors.append(f"{hypothesis['hypothesis_id']}: bundle is not represented by the family member")
        seen.add(str(sidecar.get("hypothesis_id")))
    expected = {str(row["hypothesis_id"]) for row in family.get("hypotheses", [])}
    if seen != expected:
        errors.append(f"family bundle coverage mismatch: missing={sorted(expected - seen)}, extra={sorted(seen - expected)}")
    result = {
        "status": "CERTIFICATE_INPUTS_VALID" if not errors else "CERTIFICATE_INPUTS_INVALID",
        "passed": not errors,
        "study_hash": study["configuration_hash"],
        "family_id": family.get("family_id"),
        "covered_hypotheses": len(seen),
        "expected_hypotheses": len(expected),
        "errors": errors,
        "claim_allowed": False,
    }
    target = (
        Path(out_path)
        if out_path is not None
        else Path(inputs_root) / study["configuration_hash"] / str(family.get("family_id"))
        / "certificate_inputs_validation.json"
    )
    if write_result:
        atomic_write_json(result, target)
    return {**result, "validation_artifact": str(target) if write_result else None}
