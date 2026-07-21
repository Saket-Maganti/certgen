import json
from pathlib import Path

from certgen.audit.r1b_generation_package_audit import run_audit
from certgen.core.io import read_json
from certgen.data.build_cifar10_r1_sample_package import build_sample_package
from certgen.data.build_cifar10_reference_manifest import build_reference_manifest
from certgen.generation.generate_cifar10_diffusers import _manifest_row
from certgen.generation.merge_sample_manifests import merge_sample_manifests
from certgen.generation.validate_cifar10_generated_pilot import validate_generated_pilot
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness


def _write_ppm(path: Path, *, color: bytes = b"\x00\x00\x00") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"P6\n32 32\n255\n" + color * (32 * 32))


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _generated_row(tmp_path: Path, checkpoint_id: str, seed: int, name: str, color: bytes) -> dict:
    image = tmp_path / f"{name}.ppm"
    _write_ppm(image, color=color)
    return _manifest_row(
        checkpoint_id=checkpoint_id,
        seed=seed,
        image_path=image,
        width=32,
        height=32,
        channels=3,
        generation_status="generated",
        adapter_status="ready_guarded_diffusers_ddpm_pipeline",
        device="cuda",
    )


def _has_claim_allowed_true(value):
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def test_r1b_reference_manifest_builder_tiny_fixture(tmp_path):
    root = tmp_path / "cifar"
    _write_ppm(root / "test" / "cat" / "cat_000.ppm")
    summary = build_reference_manifest(
        cifar_root=root,
        split="test",
        out_manifest=tmp_path / "reference.jsonl",
        out_summary=tmp_path / "reference_summary.json",
        license_status="license_unknown_reference_only",
        source_url="https://www.cs.toronto.edu/~kriz/cifar.html",
    )
    rows = [json.loads(line) for line in (tmp_path / "reference.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert summary["rows"] == 1
    assert rows[0]["width"] == 32
    assert rows[0]["height"] == 32
    assert rows[0]["channels"] == 3
    assert rows[0]["claim_allowed"] is False


def test_generated_manifest_validation_with_fake_samples(tmp_path):
    manifest_dir = tmp_path / "manifests"
    specs = {
        "google_ddpm_gpu0.jsonl": [_generated_row(tmp_path, "google/ddpm-cifar10-32", 0, "google", b"\x01\x02\x03")],
        "google_ddpm_gpu1.jsonl": [],
        "frank_ddpm_ema_gpu0.jsonl": [_generated_row(tmp_path, "FrankCCCCC/ddpm_ema_cifar10", 0, "ema", b"\x04\x05\x06")],
        "frank_ddpm_ema_gpu1.jsonl": [],
        "frank_cfm_gpu0.jsonl": [_generated_row(tmp_path, "FrankCCCCC/cfm-cifar10-32", 0, "cfm", b"\x07\x08\x09")],
        "frank_cfm_gpu1.jsonl": [],
    }
    for name, rows in specs.items():
        _write_jsonl(manifest_dir / name, rows)
    summary = validate_generated_pilot(
        manifest_dir=manifest_dir,
        out_manifest=tmp_path / "merged.jsonl",
        out_summary=tmp_path / "summary.json",
        expected_count_per_model=1,
        check_image_hashes=True,
    )
    assert summary["passed"], summary["errors"]
    assert summary["status_code"] == "VALIDATED_GENERATED_PILOT"
    assert summary["claim_allowed"] is False


def test_duplicate_seed_and_path_detection(tmp_path):
    row_a = _generated_row(tmp_path, "google/ddpm-cifar10-32", 1, "same", b"\x11\x11\x11")
    row_b = dict(row_a)
    row_b["sample_id"] = "different_sample_id"
    manifest = tmp_path / "dupes.jsonl"
    _write_jsonl(manifest, [row_a, row_b])
    summary = merge_sample_manifests(
        manifests=[manifest],
        out_manifest=tmp_path / "merged.jsonl",
        out_summary=tmp_path / "summary.json",
    )
    errors = "\n".join(summary["errors"])
    assert "duplicate seed" in errors
    assert "duplicate image path" in errors


def test_duplicate_sample_id_detection_in_sample_package(tmp_path):
    ref = tmp_path / "reference.ppm"
    _write_ppm(ref)
    reference_rows = [
        {
            "sample_id": "duplicate",
            "role": "reference",
            "path": str(ref),
            "source_id": "cifar10_reference",
            "width": 32,
            "height": 32,
            "channels": 3,
            "claim_allowed": False,
        }
    ]
    generated = _generated_row(tmp_path, "google/ddpm-cifar10-32", 0, "generated", b"\x22\x22\x22")
    generated["sample_id"] = "duplicate"
    _write_jsonl(tmp_path / "reference.jsonl", reference_rows)
    _write_jsonl(tmp_path / "generated.jsonl", [generated])
    summary = build_sample_package(
        reference_manifest=tmp_path / "reference.jsonl",
        generated_manifest=tmp_path / "generated.jsonl",
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        out_manifest=tmp_path / "package.jsonl",
        out_summary=tmp_path / "package_summary.json",
        expected_reference_count=1,
        expected_generated_count_per_model=1,
    )
    assert not summary["passed"]
    assert any("duplicate sample_id" in error for error in summary["errors"])


def test_readiness_before_generation_and_after_fake_valid_package(tmp_path):
    reference = tmp_path / "reference.ppm"
    _write_ppm(reference)
    manifest_before = tmp_path / "before.jsonl"
    _write_jsonl(
        manifest_before,
        [
            {"sample_id": "r", "role": "reference", "path": str(reference), "source_type": "reference_dataset", "sha256": "x", "claim_allowed": False},
            {"sample_id": "a", "role": "model_a", "path": str(tmp_path / "missing_a.ppm"), "source_type": "checkpoint_generated", "generation_status": "not_run", "claim_allowed": False},
            {"sample_id": "b", "role": "model_b", "path": str(tmp_path / "missing_b.ppm"), "source_type": "checkpoint_generated", "generation_status": "not_run", "claim_allowed": False},
        ],
    )
    before = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest=manifest_before,
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir=tmp_path / "missing_features",
        metric_reproduction_audit=tmp_path / "missing_metric.json",
        out_json=tmp_path / "before_status.json",
        report=tmp_path / "before.md",
    )
    assert before["status_code"] == "BLOCKED_GENERATION_NOT_RUN"

    rows = [
        {"sample_id": "r", "role": "reference", "path": str(reference), "source_type": "reference_dataset", "sha256": "x", "claim_allowed": False},
        _generated_row(tmp_path, "google/ddpm-cifar10-32", 0, "google_ready", b"\x31\x31\x31"),
        _generated_row(tmp_path, "FrankCCCCC/ddpm_ema_cifar10", 0, "ema_ready", b"\x32\x32\x32"),
        _generated_row(tmp_path, "FrankCCCCC/cfm-cifar10-32", 0, "cfm_ready", b"\x33\x33\x33"),
    ]
    rows[1]["role"] = "google_ddpm"
    rows[2]["role"] = "frank_ddpm_ema"
    rows[3]["role"] = "frank_cfm"
    manifest_after = tmp_path / "after.jsonl"
    _write_jsonl(manifest_after, rows)
    after = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest=manifest_after,
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir=tmp_path / "missing_features",
        metric_reproduction_audit=tmp_path / "missing_metric.json",
        out_json=tmp_path / "after_status.json",
        report=tmp_path / "after.md",
    )
    assert after["status_code"] == "READY_FOR_KAGGLE_FEATURE_EXTRACTION"
    assert after["kaggle_inception_feature_extraction_command"]
    assert after["kaggle_clip_feature_extraction_command"]


def test_no_r1b_claims_or_certificate_artifacts_and_audit_passes(tmp_path):
    audit = run_audit(out=tmp_path / "audit.md", json_out=tmp_path / "audit.json")
    assert audit["passed"], audit["checks"]
    assert audit["claim_allowed"] is False
    for path in [Path("data/results/r1b_cifar10_reference_summary.json"), Path("data/results/r1b_generated_manifest_summary.json")]:
        assert not _has_claim_allowed_true(read_json(path))
    assert not list(Path("data/results").glob("r1b*certificate*"))
