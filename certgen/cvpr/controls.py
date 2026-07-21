"""Deterministic null and obvious-gap control artifact builder."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.image_manifest import write_image_manifest
from certgen.cvpr.reference_draw import validate_canonical_reference_draw
from certgen.cvpr.study import require_frozen_study
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry


CONTROL_SCHEMA_VERSION = "certgen.cvpr.controls.v1"
CORRUPTION_LEVELS = (
    ("blur_radius_0p5", "reference_mild_corruption", 0.5),
    ("blur_radius_1p0", "reference_moderate_corruption", 1.0),
    ("blur_radius_2p0", "reference_severe_corruption", 2.0),
)
OBVIOUS_GAP_PROTOCOL = {
    "corruption_type": "gaussian_blur",
    "severity_ladder": [
        {"severity_id": severity_id, "model_id": model_id, "radius": radius}
        for severity_id, model_id, radius in CORRUPTION_LEVELS
    ],
    "primary_severe_level": "blur_radius_2p0",
    "seed": 0,
    "rationale": "A deterministic, architecture-independent degradation with no outcome-tuned severity.",
}


def _rows(path: Path) -> dict[str, dict[str, Any]]:
    values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed = {str(row.get("sample_id", "")): row for row in values}
    if len(indexed) != len(values) or "" in indexed:
        raise ValueError("reference manifest IDs must be unique and non-empty")
    return indexed


def _source_path(row: dict[str, Any], manifest: Path) -> Path:
    raw = row.get("path") or row.get("image_path")
    if not raw:
        raise ValueError("reference row has no image path")
    path = Path(str(raw))
    if path.is_absolute():
        return path
    repository_root = next(
        (
            parent
            for parent in manifest.resolve().parents
            if (parent / "pyproject.toml").is_file() and (parent / "certgen").is_dir()
        ),
        None,
    )
    if repository_root is not None:
        repository_relative = repository_root / path
        if repository_relative.is_file():
            return repository_relative
    return manifest.parent / path


def _save_rgb(
    source: Path,
    destination: Path,
    *,
    blur_radius: float | None = None,
) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        converted = image.convert("RGB")
        if blur_radius is not None:
            converted = converted.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        converted.save(destination, format="PNG", optimize=False)
        return converted.size


def _integrity(root: Path) -> dict[str, Any]:
    rows = [
        {"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": file_sha256(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "integrity_manifest.json"
    ]
    return {"schema_version": "certgen.cvpr.controls_integrity.v1", "files": rows, "claim_allowed": False}


def validate_controls(root: str | Path, *, study_hash: str | None = None, draw_hash: str | None = None) -> dict[str, Any]:
    base = Path(root)
    errors: list[str] = []
    required = {
        "null_control_manifest.json", "obvious_gap_manifest.json", "control_image_manifest.jsonl",
        "controls_summary.json", "status.json", "integrity_manifest.json",
    }
    errors.extend(f"missing control artifact: {name}" for name in sorted(required) if not (base / name).is_file())
    if errors:
        return {"passed": False, "errors": errors, "claim_allowed": False}
    status = json.loads((base / "status.json").read_text(encoding="utf-8"))
    if status.get("status") != "CONTROLS_READY" or status.get("claim_allowed") is not False:
        errors.append("control status is not ready/claim-ineligible")
    if study_hash is not None and status.get("study_hash") != study_hash:
        errors.append("control study hash mismatch")
    if draw_hash is not None and status.get("reference_draw_hash") != draw_hash:
        errors.append("control reference draw hash mismatch")
    integrity = json.loads((base / "integrity_manifest.json").read_text(encoding="utf-8"))
    for row in integrity.get("files", []):
        path = base / str(row.get("path", ""))
        if not path.is_file() or file_sha256(path) != row.get("sha256"):
            errors.append(f"control integrity mismatch: {row.get('path')}")
    return {"passed": not errors, "errors": errors, "status": status.get("status"), "claim_allowed": False}


def prepare_controls(
    *,
    study_path: str | Path,
    reference_draw: str | Path,
    out_root: str | Path = "artifacts/cvpr/controls",
    registry_path: str | Path | None = "data/artifact_registry.jsonl",
    dry_run: bool = False,
) -> dict[str, Any]:
    study = require_frozen_study(study_path)
    plan = json.loads(Path(reference_draw).read_text(encoding="utf-8"))
    verdict = validate_canonical_reference_draw(plan, study=study)
    if not verdict["passed"]:
        raise ValueError("reference draw plan invalid for controls: " + "; ".join(verdict["errors"]))
    manifest = Path(str(plan["reference_manifest_path"]))
    if not manifest.is_file() or file_sha256(manifest) != plan["source_manifest_sha256"]:
        raise ValueError("reference manifest differs from the frozen draw plan")
    indexed = _rows(manifest)
    allocations = plan["control_allocations"]
    required_allocations = {
        "null_control_split_a", "null_control_split_b", "obvious_gap_clean", "obvious_gap_corrupted"
    }
    missing = sorted(required_allocations - set(allocations))
    if missing:
        raise ValueError("selected study requires missing control allocations: " + ", ".join(missing))
    configuration_hash = stable_hash_json(
        {
            "schema_version": CONTROL_SCHEMA_VERSION,
            "study_hash": study["configuration_hash"],
            "reference_draw_hash": plan["configuration_hash"],
            "protocol": OBVIOUS_GAP_PROTOCOL,
            "allocations": allocations,
        }
    )
    target = Path(out_root) / study["configuration_hash"]
    result = {
        "status": "CONTROLS_READY",
        "controls_dir": str(target),
        "study_hash": study["configuration_hash"],
        "reference_draw_hash": plan["configuration_hash"],
        "configuration_hash": configuration_hash,
        "dry_run": dry_run,
        "evidence_class": "planning_or_input_artifact",
        "claim_allowed": False,
    }
    if dry_run:
        return result
    if target.exists():
        existing = validate_controls(target, study_hash=study["configuration_hash"], draw_hash=plan["configuration_hash"])
        status = json.loads((target / "status.json").read_text(encoding="utf-8")) if (target / "status.json").is_file() else {}
        if existing["passed"] and status.get("configuration_hash") == configuration_hash:
            return result
        raise FileExistsError(f"existing controls are not an identical valid build: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        image_rows: list[dict[str, Any]] = []
        null_rows: dict[str, list[dict[str, Any]]] = {"reference_split_a": [], "reference_split_b": []}
        null_specs = (
            ("null_control_split_a", "reference_split_a", "control_null_a"),
            ("null_control_split_b", "reference_split_b", "control_null_b"),
        )
        for allocation, model_id, role in null_specs:
            for position, source_id in enumerate(allocations[allocation]):
                source_row = indexed[str(source_id)]
                sample_id = f"{model_id}__{position:08d}"
                destination = staged / "clean_images" / model_id / f"{sample_id}.png"
                width, height = _save_rgb(_source_path(source_row, manifest), destination)
                row = {
                    "sample_id": sample_id, "role": role, "model_id": model_id,
                    "relative_image_path": destination.relative_to(staged).as_posix(),
                    "image_hash": file_sha256(destination), "seed": None,
                    "prompt_or_class_id": source_row.get("class_label"), "width": width, "height": height,
                    "mode": "RGB", "source_run_id": "control_builder:null",
                    "source_manifest_hash": plan["configuration_hash"],
                    "source_id": source_id,
                    "source_role": "reference",
                    "clean_or_corrupted": "clean",
                    "corruption_type": "none",
                    "corruption_severity": 0.0,
                    "corruption_seed": 0,
                    "reference_draw_id": source_id,
                    "study_hash": study["configuration_hash"],
                    "preprocessing_hash": study["preprocessing_hash"],
                }
                image_rows.append(row)
                null_rows[model_id].append({"sample_id": sample_id, "source_id": source_id, "draw_position": position, "image_hash": row["image_hash"], "role_id": role})
        obvious_clean: list[dict[str, Any]] = []
        obvious_corrupt: list[dict[str, Any]] = []
        corruption_ladder: dict[str, list[dict[str, Any]]] = {
            severity_id: [] for severity_id, _, _ in CORRUPTION_LEVELS
        }
        for position, source_id in enumerate(allocations["obvious_gap_clean"]):
            source_row = indexed[str(source_id)]
            clean_id = f"reference_clean__{position:08d}"
            clean_path = staged / "clean_images" / "obvious_gap" / f"{clean_id}.png"
            width, height = _save_rgb(_source_path(source_row, manifest), clean_path)
            lineage = {
                "source_id": source_id,
                "source_role": "reference",
                "corruption_seed": 0,
                "reference_draw_id": source_id,
                "study_hash": study["configuration_hash"],
                "preprocessing_hash": study["preprocessing_hash"],
            }
            clean_row = {"sample_id": clean_id, "role": "control_obvious_clean", "model_id": "reference_clean", "relative_image_path": clean_path.relative_to(staged).as_posix(), "image_hash": file_sha256(clean_path), "seed": 0, "prompt_or_class_id": source_row.get("class_label"), "width": width, "height": height, "mode": "RGB", "source_run_id": "control_builder:obvious_gap", "source_manifest_hash": plan["configuration_hash"], "clean_or_corrupted": "clean", "corruption_type": "none", "corruption_severity": 0.0, **lineage}
            image_rows.append(clean_row)
            obvious_clean.append({"sample_id": clean_id, "source_id": source_id, "output_hash": clean_row["image_hash"]})
            for severity_id, model_id, radius in CORRUPTION_LEVELS:
                corrupt_id = f"{model_id}__{position:08d}"
                corrupt_path = staged / "corrupted_images" / severity_id / f"{corrupt_id}.png"
                _save_rgb(
                    _source_path(source_row, manifest),
                    corrupt_path,
                    blur_radius=radius,
                )
                corrupt_row = {"sample_id": corrupt_id, "role": "control_obvious_corrupted", "model_id": model_id, "relative_image_path": corrupt_path.relative_to(staged).as_posix(), "image_hash": file_sha256(corrupt_path), "seed": 0, "prompt_or_class_id": source_row.get("class_label"), "width": width, "height": height, "mode": "RGB", "source_run_id": "control_builder:obvious_gap", "source_manifest_hash": plan["configuration_hash"], "clean_or_corrupted": "corrupted", "corruption_type": "gaussian_blur", "corruption_severity": radius, **lineage}
                image_rows.append(corrupt_row)
                entry = {"sample_id": corrupt_id, "source_id": source_id, "severity_id": severity_id, "radius": radius, "output_hash": corrupt_row["image_hash"]}
                corruption_ladder[severity_id].append(entry)
                if model_id == "reference_severe_corruption":
                    obvious_corrupt.append(entry)
        write_image_manifest(image_rows, staged / "control_image_manifest.jsonl", root=staged, decode=True)
        atomic_write_json({"schema_version": CONTROL_SCHEMA_VERSION, "comparison_id": "null_reference_split", "split_a": null_rows["reference_split_a"], "split_b": null_rows["reference_split_b"], "non_overlap_validated": not ({row["source_id"] for row in null_rows["reference_split_a"]} & {row["source_id"] for row in null_rows["reference_split_b"]}), "study_hash": study["configuration_hash"], "reference_draw_hash": plan["configuration_hash"], "claim_allowed": False}, staged / "null_control_manifest.json")
        atomic_write_json({"schema_version": CONTROL_SCHEMA_VERSION, "comparison_id": "obvious_gap_corruption", "protocol": OBVIOUS_GAP_PROTOCOL, "clean": obvious_clean, "corrupted": obvious_corrupt, "corruption_ladder": corruption_ladder, "dimensions": [image_rows[-1]["width"], image_rows[-1]["height"]], "color_mode": "RGB", "study_hash": study["configuration_hash"], "reference_draw_hash": plan["configuration_hash"], "sanity_control_only": True, "not_confirmatory_certificate": True, "claim_allowed": False}, staged / "obvious_gap_manifest.json")
        atomic_write_json({"null_control_status": "INPUT_ARTIFACT_READY", "obvious_gap_status": "INPUT_ARTIFACT_READY", "direction_status": "PENDING_REAL_CERTIFICATES", "preprocessing_status": "PENDING_REAL_FEATURE_EXTRACTION", "reference_draw_status": "VALIDATED", "family_operational_status": "PENDING_REAL_FEATURES", "not_empirical_evidence": True, "claim_allowed": False}, staged / "controls_summary.json")
        atomic_write_json(result, staged / "status.json")
        atomic_write_json(_integrity(staged), staged / "integrity_manifest.json")
        os.replace(staged, target)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    final_verdict = validate_controls(target, study_hash=study["configuration_hash"], draw_hash=plan["configuration_hash"])
    if not final_verdict["passed"]:
        raise ValueError("control build failed integrity validation: " + "; ".join(final_verdict["errors"]))
    if registry_path is not None:
        append_artifact_entry(
            build_artifact_entry(
                path=target / "integrity_manifest.json", artifact_type="cvpr_control_artifacts",
                stage="control_construction", run_id=study["configuration_hash"][:16], source=str(reference_draw),
                validation_status="controls_validated", evidence_class="planning_or_input_artifact",
                notes="Null and fixed Gaussian-blur control inputs; not empirical evidence.",
            ), registry_path,
        )
    return result
