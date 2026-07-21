from __future__ import annotations

import json
import pickle
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pytest

from certgen.audit.metric_reproduction import run_metric_reproduction_audit
from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.data.build_cifar10_reference_manifest import _load_pickle, build_reference_manifest
from certgen.data.cifar_reference_super_onramp import run_onramp
from certgen.notebooks.v9_static_analyzer import run_analysis
from certgen.packaging.artifact_registry import (
    append_artifact_entry,
    build_artifact_entry,
    verify_artifact_registry,
)
from certgen.packaging.common import ZipSafetyLimits, inspect_zip_safety, safe_extract_zip
from certgen.paper.v9_paper_firewall import run_firewall


def test_zip_safety_rejects_traversal_symlink_duplicate_nested_and_bomb(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../outside.txt", "bad")
    verdict = inspect_zip_safety(traversal)
    assert not verdict["passed"]
    assert "unsafe ZIP member path" in " ".join(verdict["errors"])

    symlink = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (0o120777 << 16)
    with zipfile.ZipFile(symlink, "w") as archive:
        archive.writestr(info, "target")
    assert any("symlink" in error for error in inspect_zip_safety(symlink)["errors"])

    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("A.json", "{}")
        archive.writestr("a.json", "{}")
    assert any("case-colliding" in error for error in inspect_zip_safety(duplicate)["errors"])

    nested = tmp_path / "nested.zip"
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr("inner.zip", b"not needed")
    assert any("nested archive" in error for error in inspect_zip_safety(nested)["errors"])

    bomb = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("zeros.bin", b"0" * 100_000)
    limits = ZipSafetyLimits(max_members=2, max_member_uncompressed_bytes=200_000, max_total_uncompressed_bytes=200_000, max_compression_ratio=10)
    assert any("compression ratio" in error for error in inspect_zip_safety(bomb, limits=limits)["errors"])


def test_safe_extract_is_atomic_and_never_overwrites(tmp_path: Path) -> None:
    archive_path = tmp_path / "safe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("status/result.json", "{}")
    out = tmp_path / "out"
    safe_extract_zip(archive_path, out)
    assert (out / "status/result.json").is_file()
    with pytest.raises(FileExistsError):
        safe_extract_zip(archive_path, out)


def test_artifact_registry_is_append_only_and_hash_verified(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.zip"
    artifact.write_bytes(b"package-only")
    registry = tmp_path / "registry.jsonl"
    entry = build_artifact_entry(
        path=artifact,
        artifact_type="fixture_package",
        stage="test",
        run_id="fixture-run",
        source="synthetic_fixture",
        validation_status="fixture_valid",
        evidence_class="SYNTHETIC_ONLY",
    )
    append_artifact_entry(entry, registry)
    append_artifact_entry(entry, registry)
    assert verify_artifact_registry(registry)["passed"]
    artifact.write_bytes(b"tampered")
    assert not verify_artifact_registry(registry)["passed"]


def test_artifact_registry_allows_explicit_nonretained_historical_entry(tmp_path: Path) -> None:
    registry = tmp_path / "registry.jsonl"
    row = {
        "artifact_id": "generation_input_package:" + "a" * 16,
        "path": str(tmp_path / "superseded.zip"),
        "artifact_type": "generation_input_package",
        "stage": "generation_input",
        "run_id": "historical-run",
        "source": "historical_builder",
        "hash": {"algorithm": "sha256", "value": "a" * 64},
        "created_at": "2026-01-01T00:00:00+00:00",
        "schema_version": "certgen.artifact_registry.v1",
        "validation_status": "superseded_artifact_not_retained",
        "evidence_class": "PLANNING_ONLY",
        "claim_allowed": False,
        "parent_artifacts": [],
        "notes": "Superseded planning package; rebuild from current sources before execution.",
    }
    registry.write_text(json.dumps(row) + "\n", encoding="utf-8")
    verdict = verify_artifact_registry(registry)
    assert verdict["passed"]
    assert verdict["warnings"] and not verdict["errors"]


def test_artifact_registry_accepts_content_addressed_versions_at_canonical_path(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "canonical.json"
    registry = tmp_path / "registry.jsonl"
    artifact.write_text("old\n", encoding="utf-8")
    append_artifact_entry(
        build_artifact_entry(
            path=artifact,
            artifact_type="fixture",
            stage="test",
            run_id="old",
            source="fixture",
            validation_status="valid",
            evidence_class="SYNTHETIC_ONLY",
        ),
        registry,
    )
    artifact.write_text("new\n", encoding="utf-8")
    append_artifact_entry(
        build_artifact_entry(
            path=artifact,
            artifact_type="fixture",
            stage="test",
            run_id="new",
            source="fixture",
            validation_status="valid",
            evidence_class="SYNTHETIC_ONLY",
        ),
        registry,
    )

    verdict = verify_artifact_registry(registry)

    assert verdict["passed"]
    assert any("superseded at its canonical path" in warning for warning in verdict["warnings"])


def test_firewall_guard_is_claim_scoped_not_file_scoped(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text("NO_REAL_EVIDENCE placeholder\nWe answer with real benchmarks.\n")
    payload = run_firewall(tmp_path / "out.json", tmp_path / "out.md")
    assert not payload["passed"]
    assert any(":2:" in blocker for blocker in payload["blockers"])


def test_onramp_rejects_incomplete_class_tree_and_bad_tarball(tmp_path: Path) -> None:
    incomplete = tmp_path / "incomplete"
    (incomplete / "cat").mkdir(parents=True)
    (incomplete / "ship").mkdir()
    (incomplete / "cat/a.ppm").write_bytes(b"P6\n32 32\n255\n" + b"\0" * 3072)
    payload = run_onramp(search_roots=[str(incomplete)], out_json=tmp_path / "a.json", out_report=tmp_path / "a.md")
    assert payload["materialization_can_proceed"] is False
    assert any(item["layout"] == "incomplete_image_tree" for item in payload["rejected_paths"])

    bad_tar = tmp_path / "cifar-10-python.tar.gz"
    bad_tar.write_bytes(b"not official")
    payload = run_onramp(search_roots=[str(bad_tar)], out_json=tmp_path / "b.json", out_report=tmp_path / "b.md")
    assert payload["materialization_can_proceed"] is False
    assert "MD5 mismatch" in payload["rejected_paths"][0]["reason"]


def test_onramp_records_inaccessible_candidate_instead_of_crashing(tmp_path: Path, monkeypatch) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    original = Path.iterdir

    def guarded(self):
        if self == blocked:
            raise PermissionError("fixture denied")
        return original(self)

    monkeypatch.setattr(Path, "iterdir", guarded)
    payload = run_onramp(
        search_roots=[str(blocked)],
        out_json=tmp_path / "blocked.json",
        out_report=tmp_path / "blocked.md",
    )
    assert payload["materialization_can_proceed"] is False
    assert payload["rejected_paths"][0]["layout"] == "inaccessible_directory"


def test_restricted_cifar_unpickler_and_manifest_privacy(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe_pickle"
    unsafe.write_bytes(pickle.dumps(Path("/tmp/unsafe")))
    with pytest.raises(pickle.UnpicklingError):
        _load_pickle(unsafe)

    root = tmp_path / "cifar"
    image = root / "test/cat/a.ppm"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"P6\n32 32\n255\n" + b"\0" * 3072)
    summary = build_reference_manifest(
        cifar_root=root,
        split="test",
        out_manifest=tmp_path / "manifest.jsonl",
        out_summary=tmp_path / "summary.json",
        license_status="license_unknown_reference_only",
        source_url="https://www.cs.toronto.edu/~kriz/cifar.html",
    )
    row = json.loads((tmp_path / "manifest.jsonl").read_text().splitlines()[0])
    assert summary["rows"] == 1
    assert "absolute_path" not in row


def test_smoke_metric_inputs_cannot_be_labeled_real(tmp_path: Path) -> None:
    smoke = tmp_path / "data/smoke/example"
    smoke.mkdir(parents=True)
    config = tmp_path / "metric.json"
    for name in ["ref", "model"]:
        npz = smoke / f"{name}.npz"
        np.savez_compressed(npz, features=np.arange(24, dtype=float).reshape(12, 2))
        write_json(
            {
                "feature_dim": 2,
                "n_samples": 12,
                "preprocessing": {"resize": "none", "interpolation": "none", "crop": "none", "normalization": "none"},
                "source": {"license_status": "verified_free"},
                "hashes": {"features_sha256": file_sha256(npz), "source_manifest_sha256": "smoke"},
                "created_by": "fixture",
            },
            smoke / f"{name}.json",
        )
    write_json(
        {
            "metric": "kid",
            "reference_features": {"npz": str(smoke / "ref.npz"), "sidecar": str(smoke / "ref.json")},
            "model_features": {"npz": str(smoke / "model.npz"), "sidecar": str(smoke / "model.json")},
            "expected": {"source": "none"},
        },
        config,
    )
    result = run_metric_reproduction_audit(config, tmp_path / "metric.md", tmp_path / "metric_out.json")
    assert result["evidence_status"] == "synthetic_only"
    assert result["claim_allowed"] is False


def test_repo_notebooks_pass_strengthened_static_contract() -> None:
    payload = run_analysis(out_json=Path("/tmp/certgen_notebook_audit.json"), out_report=Path("/tmp/certgen_notebook_audit.md"))
    assert payload["passed"], payload["results"]


def test_generated_execution_data_is_gitignored_but_metadata_is_not() -> None:
    ignored = subprocess.run(["git", "check-ignore", "data/kaggle_outputs/run.zip", "data/imported/run/file", "data/sources/cifar/file", "data/kaggle_inputs/input.zip"], capture_output=True, text=True, check=False)
    assert ignored.returncode == 0
    metadata = subprocess.run(["git", "check-ignore", "data/kaggle_uploads/certgen-generation/manifest.json"], capture_output=True, text=True, check=False)
    assert metadata.returncode == 1


def test_canonical_cli_status_is_claim_safe() -> None:
    completed = subprocess.run(["python3", "-m", "certgen", "status"], capture_output=True, text=True, check=True)
    payload = json.loads(completed.stdout)
    assert payload["claim_allowed"] is False
    assert payload["real_evidence_status"] == "none"
