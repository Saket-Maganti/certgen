import json
from pathlib import Path

from certgen.audit.r1a_sample_materialization_audit import run_audit
from certgen.core.io import read_json
from certgen.data.build_cifar10_reference_manifest import build_reference_manifest
from certgen.generation.generate_cifar10_diffusers import _manifest_row, main as generation_main
from certgen.generation.merge_sample_manifests import merge_sample_manifests
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness


def _write_ppm(path: Path, *, color: bytes = b"\x00\x00\x00") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"P6\n32 32\n255\n" + color * (32 * 32))


def _has_claim_allowed_true(value):
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def test_reference_manifest_builder_works_on_tiny_fake_cifar_fixture(tmp_path):
    root = tmp_path / "cifar"
    _write_ppm(root / "test" / "cat" / "cat_000.ppm")
    _write_ppm(root / "test" / "ship" / "ship_000.ppm", color=b"\xff\x00\x00")
    summary = build_reference_manifest(
        cifar_root=root,
        split="test",
        out_manifest=tmp_path / "reference.jsonl",
        out_summary=tmp_path / "summary.json",
        license_status="license_unknown_reference_only",
        source_url="https://www.cs.toronto.edu/~kriz/cifar.html",
    )
    rows = [json.loads(line) for line in (tmp_path / "reference.jsonl").read_text(encoding="utf-8").splitlines()]
    assert summary["rows"] == 2
    assert rows[0]["claim_allowed"] is False
    assert rows[0]["width"] == 32
    assert rows[0]["height"] == 32
    assert rows[0]["channels"] == 3
    assert rows[0]["sha256"]
    assert read_json(tmp_path / "summary.json")["claim_allowed"] is False


def test_generated_sample_manifest_schema_validates(tmp_path):
    image = tmp_path / "sample.ppm"
    _write_ppm(image)
    row = _manifest_row(
        checkpoint_id="google/ddpm-cifar10-32",
        seed=7,
        image_path=image,
        width=32,
        height=32,
        channels=3,
        generation_status="generated",
        adapter_status="ready_guarded_diffusers_ddpm_pipeline",
        device="cuda",
    )
    required = {"sample_id", "checkpoint_id", "seed", "image_path", "image_hash", "width", "height", "channels", "generation_status", "evidence_status", "claim_allowed"}
    assert required <= set(row)
    assert row["claim_allowed"] is False
    assert row["image_hash"]


def test_generation_cli_refuses_without_execute_and_blocks_unknown_checkpoint(tmp_path):
    rc = generation_main(
        [
            "--checkpoint-id",
            "google/ddpm-cifar10-32",
            "--seed-start",
            "0",
            "--num-samples",
            "1",
            "--out-dir",
            str(tmp_path / "out"),
            "--manifest-out",
            str(tmp_path / "manifest.jsonl"),
            "--device",
            "cpu",
        ]
    )
    assert rc == 2
    rc_unknown = generation_main(
        [
            "--checkpoint-id",
            "unknown/model",
            "--seed-start",
            "0",
            "--num-samples",
            "1",
            "--out-dir",
            str(tmp_path / "out"),
            "--manifest-out",
            str(tmp_path / "manifest.jsonl"),
            "--device",
            "cpu",
            "--dry-run",
        ]
    )
    assert rc_unknown == 2


def test_merge_sample_manifests_detects_duplicate_seed(tmp_path):
    image_a = tmp_path / "a.ppm"
    image_b = tmp_path / "b.ppm"
    _write_ppm(image_a)
    _write_ppm(image_b, color=b"\x01\x02\x03")
    rows = [
        _manifest_row(
            checkpoint_id="google/ddpm-cifar10-32",
            seed=1,
            image_path=image_a,
            width=32,
            height=32,
            channels=3,
            generation_status="generated",
            adapter_status="ready_guarded_diffusers_ddpm_pipeline",
            device="cuda",
        ),
        _manifest_row(
            checkpoint_id="google/ddpm-cifar10-32",
            seed=1,
            image_path=image_b,
            width=32,
            height=32,
            channels=3,
            generation_status="generated",
            adapter_status="ready_guarded_diffusers_ddpm_pipeline",
            device="cuda",
        ),
    ]
    manifest = tmp_path / "dupes.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary = merge_sample_manifests(
        manifests=[manifest],
        out_manifest=tmp_path / "merged.jsonl",
        out_summary=tmp_path / "summary.json",
    )
    assert not summary["passed"]
    assert any("duplicate seed" in error for error in summary["errors"])


def test_r1_readiness_distinguishes_generation_and_feature_blockers(tmp_path):
    reference = tmp_path / "reference.ppm"
    model_a = tmp_path / "model_a.ppm"
    model_b = tmp_path / "model_b.ppm"
    _write_ppm(reference)
    rows_generation_missing = [
        {"sample_id": "r", "role": "reference", "path": str(reference), "source_type": "reference_dataset", "claim_allowed": False},
        {"sample_id": "a", "role": "model_a", "path": str(model_a), "source_type": "checkpoint_generated", "generation_status": "not_run", "claim_allowed": False},
        {"sample_id": "b", "role": "model_b", "path": str(model_b), "source_type": "checkpoint_generated", "generation_status": "not_run", "claim_allowed": False},
    ]
    manifest = tmp_path / "generation_missing.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in rows_generation_missing) + "\n", encoding="utf-8")
    status = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest=manifest,
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir=tmp_path / "missing_features",
        metric_reproduction_audit=tmp_path / "missing_metric.json",
        out_json=tmp_path / "status_generation.json",
        report=tmp_path / "status_generation.md",
    )
    assert status["status_code"] == "BLOCKED_GENERATION_NOT_RUN"

    _write_ppm(model_a, color=b"\x11\x22\x33")
    _write_ppm(model_b, color=b"\x44\x55\x66")
    rows_ready_for_features = [
        {"sample_id": "r", "role": "reference", "path": str(reference), "source_type": "reference_dataset", "sha256": "x", "claim_allowed": False},
        {"sample_id": "a", "role": "model_a", "path": str(model_a), "source_type": "checkpoint_generated", "generation_status": "generated", "sha256": "y", "claim_allowed": False},
        {"sample_id": "b", "role": "model_b", "path": str(model_b), "source_type": "checkpoint_generated", "generation_status": "generated", "sha256": "z", "claim_allowed": False},
    ]
    manifest_ready = tmp_path / "ready_for_features.jsonl"
    manifest_ready.write_text("\n".join(json.dumps(row) for row in rows_ready_for_features) + "\n", encoding="utf-8")
    ready_status = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest=manifest_ready,
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir=tmp_path / "missing_features",
        metric_reproduction_audit=tmp_path / "missing_metric.json",
        out_json=tmp_path / "status_features.json",
        report=tmp_path / "status_features.md",
    )
    assert ready_status["status_code"] == "READY_FOR_KAGGLE_FEATURE_EXTRACTION"
    assert ready_status["kaggle_feature_extraction_ready"] is True


def test_r1a_artifacts_are_claim_safe_and_audit_passes(tmp_path):
    for path in [
        Path("data/results/r1_source_selection_status.json"),
        Path("data/results/r1_cifar10_status.json"),
    ]:
        if path.exists():
            assert not _has_claim_allowed_true(read_json(path))
    audit = run_audit(out=tmp_path / "audit.md", json_out=tmp_path / "audit.json")
    assert audit["passed"], audit["checks"]
    assert audit["claim_allowed"] is False
