from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from certgen.discovery import classify_package, discover_asset_mount, discover_wheelhouse
from certgen.discovery.expected_output import discover_expected_output
from certgen.discovery.simulation import write_synthetic_package
from certgen.notebooks.cvpr_factory import input_discovery_code
from certgen.notebooks.final_zip import (
    reassemble_multipart_fallback,
    write_multipart_fallback,
)
from certgen.notebooks.environment_bootstrap import COMPATIBILITY_PROFILES, bootstrap_environment
from certgen.notebooks.trusted_bootstrap import (
    AuthenticationError,
    authenticate_candidate,
    discover_authenticated_package,
)


def _expected(path: Path) -> dict[str, object]:
    candidate = classify_package(path)
    assert candidate.valid and candidate.package_sha256
    identity = candidate.identity
    return {
        "schema_version": "certgen.expected_package_identity.v1",
        "expected_package_sha256": candidate.package_sha256,
        "expected_scientific_identity_hash": identity.scientific_identity_hash,
        "expected_configuration_hash": identity.configuration_hash,
        "expected_run_id": identity.run_id,
        "expected_study_hash": identity.study_hash,
        "expected_profile_id": identity.profile_id,
        "expected_scale": identity.scale,
        "expected_source_code_hash": identity.source_code_hash,
        "expected_integrity_manifest": identity.integrity_manifest,
        "expected_output_schema_version": identity.output_schema_version,
        "expected_package_type": identity.package_type.value,
        "expected_stage": identity.stage,
        "claim_allowed": False,
    }


def _rewrite_zip(source: Path, output: Path, changes: dict[str, bytes], *, extra: tuple[str, bytes] | None = None) -> None:
    with zipfile.ZipFile(source) as archive:
        members = {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}
    members.update(changes)
    if extra is not None:
        members[extra[0]] = extra[1]
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def test_preimport_gate_verifies_all_code_members_and_exact_identity(tmp_path: Path) -> None:
    package = write_synthetic_package(tmp_path / "renamed-input.zip", stage="diagnostic")
    expected = _expected(package)
    authenticated = authenticate_candidate(package, expected)
    assert authenticated["source_code_hash"] == expected["expected_source_code_hash"]

    modified = tmp_path / "modified-code.zip"
    _rewrite_zip(package, modified, {"certgen/__init__.py": b"modified after manifest\n"})
    with pytest.raises(AuthenticationError, match="integrity|source code"):
        authenticate_candidate(modified, {**expected, "expected_package_sha256": None})

    extra = tmp_path / "extra-file.zip"
    _rewrite_zip(package, extra, {}, extra=("unexpected.py", b"pass\n"))
    with pytest.raises(AuthenticationError, match="membership"):
        authenticate_candidate(extra, {**expected, "expected_package_sha256": None})

    with pytest.raises(AuthenticationError, match="exact expected identity"):
        authenticate_candidate(package, {**expected, "expected_run_id": "stale-run"})
    with pytest.raises(AuthenticationError, match="exact expected identity"):
        authenticate_candidate(package, {**expected, "expected_package_sha256": "0" * 64})


def test_preimport_gate_blocks_unsafe_archives_and_extracted_symlinks(tmp_path: Path) -> None:
    expected = {"expected_package_type": "DIAGNOSTIC_INPUT", "expected_stage": "diagnostic"}
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape", b"bad")
    with pytest.raises(AuthenticationError, match="unsafe package member"):
        authenticate_candidate(traversal, expected)

    special = tmp_path / "special.zip"
    info = zipfile.ZipInfo("device")
    info.create_system = 3
    info.external_attr = (stat.S_IFCHR | 0o600) << 16
    with zipfile.ZipFile(special, "w") as archive:
        archive.writestr(info, b"bad")
    with pytest.raises(AuthenticationError, match="special archive"):
        authenticate_candidate(special, expected)

    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("A", b"one")
        archive.writestr("a", b"two")
    with pytest.raises(AuthenticationError, match="case-colliding"):
        authenticate_candidate(duplicate, expected)

    extracted = write_synthetic_package(tmp_path / "extracted", stage="diagnostic", extracted=True)
    (extracted / "link").symlink_to(extracted / "payload.txt")
    with pytest.raises(AuthenticationError, match="symlink"):
        authenticate_candidate(extracted, {**_expected(write_synthetic_package(tmp_path / "source.zip", stage="diagnostic")), "expected_package_sha256": None})


def test_identical_authenticated_copies_dedupe_and_conflicting_content_fails(tmp_path: Path) -> None:
    first = write_synthetic_package(tmp_path / "a.zip", stage="diagnostic")
    expected = _expected(first)
    shutil.copy2(first, tmp_path / "nested" / "b.zip") if (tmp_path / "nested").mkdir() is None else None
    result = discover_authenticated_package([tmp_path], expected)
    assert result["selection_status"] == "DUPLICATE_IDENTICAL_COPY_DEDUPED"

    conflicting = write_synthetic_package(tmp_path / "other.zip", stage="diagnostic", run_id="other-run")
    broad = {key: value for key, value in expected.items() if key not in {"expected_package_sha256", "expected_run_id", "expected_scientific_identity_hash", "expected_configuration_hash"}}
    with pytest.raises(AuthenticationError, match="AMBIGUOUS_DIFFERENT_CONTENT"):
        discover_authenticated_package([tmp_path], broad)
    assert conflicting.is_file()


def test_notebook_embeds_frozen_bootstrap_hash_and_generic_requires_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    code = input_discovery_code("generation", require_explicit_identity=True)
    assert "_TRUSTED_BOOTSTRAP_SHA256" in code
    assert "explicit CERTGEN_EXPECTED_PACKAGE_IDENTITY_JSON is required" in code
    corrupted = code.replace(
        '_TRUSTED_BOOTSTRAP_SHA256 = "',
        '_TRUSTED_BOOTSTRAP_SHA256 = "0',
        1,
    )
    monkeypatch.delenv("CERTGEN_EXPECTED_PACKAGE_IDENTITY_JSON", raising=False)
    with pytest.raises(RuntimeError, match="trusted bootstrap source hash mismatch"):
        exec(compile(corrupted, "<corrupt-notebook>", "exec"), {})


def _model_asset_manifest(snapshot: Path, file_path: Path) -> dict[str, object]:
    relative = file_path.relative_to(snapshot).as_posix()
    return {
        "schema_version": "certgen.model_asset_manifest.v2",
        "asset_id": "demo__asset",
        "model_or_extractor_id": "demo",
        "revision": "rev-1",
        "source": "synthetic/demo",
        "license": "synthetic_fixture_only",
        "authentication_required": False,
        "files": [relative],
        "file_hashes": {relative: hashlib.sha256(file_path.read_bytes()).hexdigest()},
        "total_size": file_path.stat().st_size,
        "cache_root": ".",
        "asset_root": ".",
        "snapshot_path": ".",
        "portable_snapshot_root": True,
        "source_repo": "synthetic/demo",
        "layout_type": "direct_local_snapshot",
        "loader_type": "from_pretrained_local_snapshot",
        "policy": "OFFLINE_PACKAGED_CACHE",
        "validated_at": "synthetic_fixture",
        "validation_status": "VALIDATED",
        "preflight_status": "ASSET_VALIDATED",
        "redistribution_allowed": False,
        "public_archive_included": False,
        "user_provided": True,
        "private_mount_required": True,
        "license_source": "synthetic/demo",
        "license_status": "synthetic_fixture_only",
        "claim_allowed": False,
    }


def _asset_mount(root: Path, payload: bytes = b"weights") -> Path:
    snapshot = root / "snapshot"
    snapshot.mkdir(parents=True)
    weight = snapshot / "weights.bin"
    weight.write_bytes(payload)
    per_asset = root / "demo.asset.json"
    per_asset.write_text(json.dumps(_model_asset_manifest(snapshot, weight)), encoding="utf-8")
    aggregate = {
        "schema_version": "certgen.aggregate_asset_manifest.v2",
        "files": [
            {
                "path": "snapshot/weights.bin",
                "size": weight.stat().st_size,
                "sha256": hashlib.sha256(weight.read_bytes()).hexdigest(),
                "asset_id": "demo__asset",
                "model_or_extractor_id": "demo",
                "revision": "rev-1",
                "snapshot_root": "snapshot",
                "asset_manifest": "demo.asset.json",
                "loader_type": "from_pretrained_local_snapshot",
                "license_status": "synthetic_fixture_only",
            }
        ],
        "claim_allowed": False,
    }
    (root / "asset_manifest.json").write_text(json.dumps(aggregate), encoding="utf-8")
    return root


def test_asset_mount_resolution_dedupes_identical_and_rejects_conflicts(tmp_path: Path) -> None:
    first = _asset_mount(tmp_path / "alpha")
    unique = discover_asset_mount([first], required_assets={"demo__asset": "rev-1"})
    assert unique["status"] == "SELECTED_UNIQUE_VALID_ASSET_MOUNT"
    assert unique["selected"]["resolution_map"]["demo__asset"]["snapshot_root"] == str(first / "snapshot")

    _asset_mount(tmp_path / "beta")
    deduped = discover_asset_mount([tmp_path], required_assets={"demo__asset": "rev-1"})
    assert deduped["status"] == "DUPLICATE_IDENTICAL_COPY_DEDUPED"
    _asset_mount(tmp_path / "gamma", b"different weights")
    ambiguous = discover_asset_mount([tmp_path], required_assets={"demo__asset": "rev-1"})
    assert ambiguous["status"] == "AMBIGUOUS_DIFFERENT_CONTENT"


def _wheelhouse(root: Path, filename: str) -> None:
    root.mkdir(parents=True)
    wheel = root / filename
    wheel.write_bytes(b"synthetic wheel")
    manifest = {
        "schema_version": "certgen.wheelhouse_manifest.v2",
        "profiles": ["kaggle_t4x2_diagnostic"],
        "target_python": "cp311",
        "platforms": ["manylinux_x86_64"],
        "files": [
            {
                "path": filename,
                "size": wheel.stat().st_size,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            }
        ],
        "claim_allowed": False,
    }
    (root / "wheelhouse_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_exact_wheelhouse_validates_version_and_kaggle_tags(tmp_path: Path) -> None:
    _wheelhouse(tmp_path / "correct", "demo-1.2.3-py3-none-any.whl")
    correct = discover_wheelhouse(
        [tmp_path / "correct"],
        profile="kaggle_t4x2_diagnostic",
        required_requirements=["demo==1.2.3"],
    )
    assert correct["status"] == "SELECTED_UNIQUE_VALID_WHEELHOUSE"
    _wheelhouse(tmp_path / "wrong-version", "demo-9.9.9-py3-none-any.whl")
    wrong_version = discover_wheelhouse(
        [tmp_path / "wrong-version"],
        profile="kaggle_t4x2_diagnostic",
        required_requirements=["demo==1.2.3"],
    )
    assert "WHEEL_VERSION_MISMATCH" in " ".join(wrong_version["candidates"][0]["errors"])
    _wheelhouse(tmp_path / "wrong-tag", "demo-1.2.3-cp312-cp312-macosx_14_0_arm64.whl")
    wrong_tag = discover_wheelhouse(
        [tmp_path / "wrong-tag"],
        profile="kaggle_t4x2_diagnostic",
        required_requirements=["demo==1.2.3"],
    )
    assert "WHEEL_TAG_INCOMPATIBLE" in " ".join(wrong_tag["candidates"][0]["errors"])


def test_multipart_reassembly_is_atomic_and_package_validated(tmp_path: Path) -> None:
    source = write_synthetic_package(tmp_path / "output.zip", stage="diagnostic", direction="output")
    manifest = write_multipart_fallback(source, maximum_part_bytes=200)
    manifest_path = source.with_suffix(source.suffix + ".parts.json")
    assert len(manifest["parts"]) > 1
    source.unlink()
    rebuilt = reassemble_multipart_fallback(manifest_path, output_path=tmp_path / "renamed-return.zip")
    assert rebuilt["passed"] is True
    assert classify_package(tmp_path / "renamed-return.zip").valid
    (tmp_path / manifest["parts"][0]["path"]).write_bytes(b"corrupt")
    failed = reassemble_multipart_fallback(manifest_path, output_path=tmp_path / "another.zip")
    assert failed["passed"] is False


def test_local_resume_binds_active_input_and_dedupes_only_identical_bytes(tmp_path: Path) -> None:
    active = write_synthetic_package(
        tmp_path
        / "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
        stage="diagnostic",
    )
    input_sha = str(classify_package(active).package_sha256)
    returned = write_synthetic_package(
        tmp_path / "downloads/arbitrarily-renamed.zip",
        stage="diagnostic",
        direction="output",
        input_package_sha256=input_sha,
    )
    write_synthetic_package(
        tmp_path / "downloads/stale.zip",
        stage="diagnostic",
        direction="output",
        run_id="stale-run",
        input_package_sha256=input_sha,
    )
    selected = discover_expected_output(tmp_path, "diagnostic", [tmp_path / "downloads"])
    assert selected["status"] == "SELECTED_UNIQUE_VALID_PACKAGE"
    assert Path(selected["selected"]["path"]) == returned

    shutil.copy2(returned, tmp_path / "downloads/identical-copy.zip")
    deduped = discover_expected_output(tmp_path, "diagnostic", [tmp_path / "downloads"])
    assert deduped["status"] == "DUPLICATE_IDENTICAL_COPY_DEDUPED"

    with zipfile.ZipFile(returned) as archive:
        members = {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}
    with zipfile.ZipFile(tmp_path / "downloads/different-container.zip", "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            archive.writestr(name, data)
    ambiguous = discover_expected_output(tmp_path, "diagnostic", [tmp_path / "downloads"])
    assert ambiguous["status"] == "AMBIGUOUS_DIFFERENT_CONTENT"


def test_restart_marker_is_input_bound_auto_detected_and_consumed(tmp_path: Path) -> None:
    profile = "kaggle_t4x2_diagnostic"
    compatible_candidates = ("2.7.1", "2.0.2", "6.0.2", "25.0")
    expected_versions = {
        requirement.name: next(
            value for value in compatible_candidates if value in requirement.specifier
        )
        for requirement in (Requirement(raw) for raw in COMPATIBILITY_PROFILES[profile])
    }
    installed: dict[str, str] = {}

    def installer(command, **kwargs):  # type: ignore[no-untyped-def]
        installed.update(expected_versions)
        return subprocess.CompletedProcess(command, 0, stdout="installed", stderr="")

    def pip_check(*args, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(args[0], 0, stdout="ok", stderr="")

    identity = {"package_sha256": "a" * 64, "scientific_identity_hash": "b" * 64}
    first = bootstrap_environment(
        profile,
        output_dir=tmp_path,
        network_allowed=True,
        apply=True,
        install_mode="KAGGLE_INTERNET_ON_INSTALL",
        version_getter=installed.get,
        installer=installer,
        pip_checker=pip_check,
        expected_input_identity=identity,
    )
    assert first["status"] == "KERNEL_RESTART_REQUIRED"
    assert (tmp_path / "kernel_restart_required.json").is_file()
    second = bootstrap_environment(
        profile,
        output_dir=tmp_path,
        network_allowed=True,
        apply=True,
        install_mode="KAGGLE_INTERNET_ON_INSTALL",
        version_getter=installed.get,
        pip_checker=pip_check,
        importer=lambda name: object(),
        expected_input_identity=identity,
    )
    assert second["status"] == "ENVIRONMENT_COMPATIBLE"
    assert second["restart_marker_consumed"] is True
    assert not (tmp_path / "kernel_restart_required.json").exists()
