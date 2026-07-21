import csv
import json
import zipfile
from pathlib import Path

import numpy as np

from certgen.core.hashing import file_sha256
from certgen.packaging.build_kaggle_feature_input_zip import build_feature_input_zip
from certgen.packaging.build_kaggle_generation_input_zip import build_generation_input_zip
from certgen.packaging.validate_kaggle_feature_output_zip import validate_feature_output_zip
from certgen.packaging.validate_kaggle_generation_output_zip import validate_generation_output_zip
from certgen.pipeline.v6_execution import write_final_execution_audit


ROLES = ["reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"]
MODELS = {
    "google_ddpm": "google/ddpm-cifar10-32",
    "frank_ddpm_ema": "FrankCCCCC/ddpm_ema_cifar10",
    "frank_cfm": "FrankCCCCC/cfm-cifar10-32",
}
PREPROCESSING = {"image_size": 32, "resize_policy": "fixed_32", "interpolation": "bilinear", "crop": "none", "normalization": "inception"}


def _write_ppm(path: Path, color: bytes = b"\x00\x00\x00") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"P6\n32 32\n255\n" + color * 32 * 32)


def _write_ledger(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model_id", "source_url", "license_status", "provenance_status"])
        writer.writeheader()
        writer.writerow({"model_id": "cifar10_reference", "source_url": "https://www.cs.toronto.edu/~kriz/cifar.html", "license_status": "license_unknown_reference_only", "provenance_status": "planned"})
        for model in MODELS.values():
            writer.writerow({"model_id": model, "source_url": "https://huggingface.co", "license_status": "allowed", "provenance_status": "planned"})


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _reference_rows(tmp_path: Path) -> list[dict]:
    image = tmp_path / "reference" / "cifar10_test_000.ppm"
    _write_ppm(image)
    return [{"sample_id": "ref_000", "role": "reference", "path": str(image), "width": 32, "height": 32, "channels": 3, "sha256": file_sha256(image), "source_id": "cifar10_reference", "claim_allowed": False}]


def _generated_rows(tmp_path: Path) -> list[dict]:
    rows = []
    for idx, (role, checkpoint) in enumerate(MODELS.items()):
        image = tmp_path / "generated" / role / "seed_000.ppm"
        _write_ppm(image, bytes([idx + 1, idx + 2, idx + 3]))
        rows.append(
            {
                "sample_id": f"{role}_000",
                "role": role,
                "checkpoint_id": checkpoint,
                "seed": 0,
                "path": str(image),
                "image_path": str(image),
                "width": 32,
                "height": 32,
                "channels": 3,
                "sha256": file_sha256(image),
                "image_hash": file_sha256(image),
                "generation_status": "generated",
                "claim_allowed": False,
            }
        )
    return rows


def _write_feature_cache(path: Path, role: str, extractor: str, features: np.ndarray) -> None:
    npz = path / "split" / f"{role}_{extractor}.npz"
    sidecar = path / "split" / f"{role}_{extractor}.sidecar.json"
    npz.parent.mkdir(parents=True, exist_ok=True)
    sample_ids = np.asarray([f"{role}_{idx:03d}" for idx in range(features.shape[0])])
    np.savez_compressed(npz, features=features.astype(np.float32), sample_ids=sample_ids)
    payload = {
        "extractor": "inception_v3_pool3" if extractor == "inception" else "clip_vit",
        "feature_extractor": "inception_v3_pool3" if extractor == "inception" else "clip_vit",
        "feature_dim": int(features.shape[1]),
        "n_samples": int(features.shape[0]),
        "num_items": int(features.shape[0]),
        "sample_ids": sample_ids.tolist(),
        "feature_path": str(npz),
        "features_sha256": file_sha256(npz),
        "hash": file_sha256(npz),
        "preprocessing": PREPROCESSING,
        "source": {"license_status": "allowed"},
        "hashes": {"features_sha256": file_sha256(npz), "source_manifest_sha256": "fixture", "preprocessing_lock_sha256": "fixture"},
        "created_by": "test_v6_cpu_kaggle_packaging",
        "evidence_status": "real_features_unvalidated",
        "claim_allowed": False,
    }
    sidecar.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_generation_input_zip_builder_inspects_clean_package(tmp_path):
    ledger = tmp_path / "ledger.csv"
    _write_ledger(ledger)
    out_zip = tmp_path / "generation.zip"
    manifest = build_generation_input_zip(provenance_ledger=ledger, out_zip=out_zip, manifest_out=tmp_path / "manifest.json")
    assert manifest["passed"]
    with zipfile.ZipFile(out_zip) as zf:
        names = set(zf.namelist())
        assert "README.md" in names
        assert "config/checkpoints.json" in names
        assert "config/seed_shard_plan.json" in names
        joined = "\n".join(names) + "\n" + zf.read("metadata/package_manifest.json").decode()
    assert "claim_allowed\": true" not in joined.lower()
    assert "data/results" not in joined
    assert "/Users/" not in joined


def test_generation_output_zip_validator_on_fake_small_zip(tmp_path):
    output_zip = tmp_path / "generation_outputs.zip"
    rows_by_name = {}
    for idx, (role, checkpoint) in enumerate(MODELS.items()):
        rows_by_name[f"{role}_gpu0.jsonl"] = []
        rows_by_name[f"{role}_gpu1.jsonl"] = []
        image = tmp_path / "zip_src" / "samples" / role / "gpu0" / f"{role}_seed_000.ppm"
        _write_ppm(image, bytes([idx + 1, idx + 3, idx + 5]))
        rows_by_name[f"{role}_gpu0.jsonl"].append(
            {
                "sample_id": f"{role}_000",
                "checkpoint_id": checkpoint,
                "seed": 0,
                "image_path": str(image),
                "width": 32,
                "height": 32,
                "channels": 3,
                "image_hash": file_sha256(image),
                "generation_status": "generated",
                "claim_allowed": False,
            }
        )
    with zipfile.ZipFile(output_zip, "w") as zf:
        for role in MODELS:
            image = tmp_path / "zip_src" / "samples" / role / "gpu0" / f"{role}_seed_000.ppm"
            zf.write(image, f"samples/{role}/gpu0/{role}_seed_000.ppm")
        for name, rows in rows_by_name.items():
            zf.writestr(f"manifests/{name}", "\n".join(json.dumps(row) for row in rows) + ("\n" if rows else ""))
    summary = validate_generation_output_zip(
        input_zip=output_zip,
        extract_dir=tmp_path / "extract",
        out_manifest=tmp_path / "merged.jsonl",
        summary_out=tmp_path / "summary.json",
        expected_count_per_model=1,
    )
    assert summary["passed"], summary["errors"]
    assert summary["status_code"] == "VALIDATED_GENERATED_PILOT"


def test_feature_input_zip_builder_sanitizes_paths(tmp_path):
    ledger = tmp_path / "ledger.csv"
    lock = tmp_path / "lock.json"
    _write_ledger(ledger)
    lock.write_text(json.dumps(PREPROCESSING | {"lock_id": "fixture"}), encoding="utf-8")
    reference = tmp_path / "reference.jsonl"
    generated = tmp_path / "generated.jsonl"
    samples = tmp_path / "samples.jsonl"
    rows = _reference_rows(tmp_path) + _generated_rows(tmp_path)
    _write_jsonl(reference, rows[:1])
    _write_jsonl(generated, rows[1:])
    _write_jsonl(samples, rows)
    out_zip = tmp_path / "features.zip"
    manifest = build_feature_input_zip(
        reference_manifest=reference,
        generated_manifest=generated,
        sample_manifest=samples,
        provenance_ledger=ledger,
        preprocessing_lock=lock,
        out_zip=out_zip,
        manifest_out=tmp_path / "feature_manifest.json",
        expected_reference_count=1,
        expected_generated_count_per_model=1,
    )
    assert manifest["passed"], manifest["errors"]
    with zipfile.ZipFile(out_zip) as zf:
        text = "\n".join(zf.namelist()) + zf.read("manifests/cifar10_r1_feature_extraction_samples.jsonl").decode()
    assert "/Users/" not in text
    assert "user_provided_local_path_redacted" in text
    assert "claim_allowed\": true" not in text.lower()


def test_feature_output_zip_validator_on_fake_small_zip(tmp_path):
    feature_root = tmp_path / "feature_src"
    rng = np.random.default_rng(3)
    for extractor in ["inception", "clip"]:
        for role in ROLES:
            _write_feature_cache(feature_root, role, extractor, rng.normal(size=(8, 4)))
    output_zip = tmp_path / "feature_outputs.zip"
    with zipfile.ZipFile(output_zip, "w") as zf:
        for path in (feature_root / "split").iterdir():
            zf.write(path, f"split/{path.name}")
    summary = validate_feature_output_zip(input_zip=output_zip, extract_dir=tmp_path / "extract_features", summary_out=tmp_path / "feature_summary.json")
    assert summary["passed"], summary["errors"]
    assert summary["status_code"] == "FEATURE_OUTPUT_ZIP_VALIDATED"


def test_notebooks_and_runtime_docs_have_required_boundaries():
    gen_nb = Path("notebooks/kaggle/certgen_cifar10_generation_t4x2_1k.ipynb").read_text(encoding="utf-8")
    feat_nb = Path("notebooks/kaggle/certgen_cifar10_feature_extraction_t4x2_1k.ipynb").read_text(encoding="utf-8")
    assert "CUDA_VISIBLE_DEVICES=0" in gen_nb and "CUDA_VISIBLE_DEVICES=1" in gen_nb
    assert "certgen_cifar10_generated_1k_outputs.zip" in gen_nb
    assert "This notebook generates sample-package artifacts only" in gen_nb
    assert "CUDA_VISIBLE_DEVICES=0" in feat_nb and "CUDA_VISIBLE_DEVICES=1" in feat_nb
    assert "certgen_cifar10_features_1k_outputs.zip" in feat_nb
    assert "does not run certificates" in feat_nb
    assert "certify_clean_metric" not in gen_nb
    assert "certify_clean_metric" not in feat_nb
    assert "planning estimates only, not empirical project results" in Path("docs/KAGGLE_T4X2_GENERATION_RUNTIME_ESTIMATES_V6.md").read_text(encoding="utf-8")
    assert "planning estimates only, not empirical project results" in Path("docs/KAGGLE_T4X2_FEATURE_EXTRACTION_RUNTIME_ESTIMATES_V6.md").read_text(encoding="utf-8")


def test_v6_cpu_command_bundle_and_final_audit_taxonomy(tmp_path):
    expected = [
        "00_check_local_prereqs.sh",
        "01_materialize_reference_from_local_root.sh",
        "01b_materialize_reference_from_official_archive.sh",
        "02_validate_reference_manifest.sh",
        "03_create_kaggle_generation_input_zip.sh",
        "04_validate_copied_back_generation_outputs.sh",
        "05_build_feature_extraction_sample_package.sh",
        "06_create_kaggle_feature_extraction_input_zip.sh",
        "07_validate_copied_back_feature_caches.sh",
        "08_split_feature_caches_by_role.sh",
        "09_run_metric_reproduction_and_sanity_gates.sh",
        "10_run_first_certificate_pilot_if_ready.sh",
        "11_run_final_execution_audit.sh",
    ]
    for name in expected:
        text = (Path("commands/v6_cpu_execution") / name).read_text(encoding="utf-8")
        assert "set -euo pipefail" in text
        assert "PYTHONDONTWRITEBYTECODE=1" in text
        assert 'CUDA_VISIBLE_DEVICES=""' in text
    audit = write_final_execution_audit(out_json=tmp_path / "final.json", report=tmp_path / "final.md")
    assert audit["status_code"] in {
        "BLOCKED_MISSING_REFERENCE_SAMPLES",
        "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING",
        "BLOCKED_GENERATED_MANIFEST_INVALID",
        "BLOCKED_FEATURE_INPUT_PACKAGE_MISSING",
        "BLOCKED_FEATURE_OUTPUT_ZIP_MISSING",
        "BLOCKED_FEATURE_CACHE_INVALID",
        "BLOCKED_METRIC_REPRODUCTION_OR_SANITY",
        "READY_FOR_FIRST_CERTIFICATE_PILOT",
        "FIRST_PILOT_COMPLETED_NO_CLAIM",
        "FIRST_PILOT_FAILED_GATES",
    }
    assert audit["claim_allowed"] is False
