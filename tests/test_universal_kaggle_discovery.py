from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import zipfile
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from certgen.discovery import (
    DiscoveryLimits,
    PackageRequirement,
    PackageType,
    SelectionStatus,
    classify_package,
    discover_asset_mount,
    discover_packages,
    discover_wheelhouse,
    materialize_selected_package,
)
from certgen.discovery.simulation import (
    FIXTURE_LABELS,
    run_four_account_matrix,
    write_synthetic_package,
)
from certgen.notebooks.environment_bootstrap import (
    COMPATIBILITY_PROFILES,
    _lock_requirements,
    bootstrap_environment,
)


def _requirement(stage: str = "diagnostic") -> PackageRequirement:
    return PackageRequirement(
        expected_package_type=PackageType[f"{stage.upper()}_INPUT"],
        expected_stage=stage,
        expected_study_hash="a" * 64,
        expected_profile_id="synthetic-portability-profile",
        expected_scale="fixture",
        required_completion_status="INPUT_PACKAGE_READY",
    )


def test_arbitrary_name_depth_unrelated_candidates_and_materialization(tmp_path: Path) -> None:
    source = write_synthetic_package(
        tmp_path / "account-random" / "deep" / "a" / "b" / "renamed-anything.zip",
        stage="diagnostic",
    )
    write_synthetic_package(tmp_path / "wrong-stage.zip", stage="preflight")
    write_synthetic_package(tmp_path / "wrong-study.zip", stage="diagnostic", study_hash="b" * 64)
    (tmp_path / "notes.zip").write_bytes(b"unrelated")
    result = discover_packages((tmp_path,), requirement=_requirement())
    assert result.status is SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE
    assert result.selected and result.selected.path == source
    output = materialize_selected_package(result.selected, destination=tmp_path / "working" / "selected")
    assert output.is_dir()
    assert classify_package(output).valid
    assert (output / ".certgen_runtime_location.json").is_file()


def test_extracted_package_extra_file_and_duplicate_exact_matches_fail_closed(tmp_path: Path) -> None:
    extracted = write_synthetic_package(tmp_path / "auto-expanded", stage="preflight", extracted=True)
    selected = discover_packages((tmp_path,), requirement=_requirement("preflight"))
    assert selected.status is SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE
    (extracted / "unexpected.txt").write_text("extra", encoding="utf-8")
    assert not classify_package(extracted).valid

    first = write_synthetic_package(tmp_path / "one.zip", stage="generation")
    second = write_synthetic_package(tmp_path / "nested" / "two.zip", stage="generation")
    ambiguous = discover_packages((tmp_path,), requirement=_requirement("generation"))
    assert ambiguous.status is SelectionStatus.AMBIGUOUS_MATCHING_PACKAGES
    assert {row.path for row in ambiguous.matching_candidates} == {first, second}
    assert ambiguous.selected is None


def test_archive_traversal_symlink_case_collision_and_limits_are_rejected(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape", b"bad")
    assert any("unsafe archive member path" in error for error in classify_package(traversal).errors)

    symlink = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = 0o120777 << 16
    with zipfile.ZipFile(symlink, "w") as archive:
        archive.writestr(info, b"target")
    assert any("symlink" in error for error in classify_package(symlink).errors)

    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("A.json", b"{}")
        archive.writestr("a.json", b"{}")
    assert any("case-folded" in error for error in classify_package(duplicate).errors)

    oversized = write_synthetic_package(tmp_path / "oversized.zip", stage="diagnostic")
    candidate = classify_package(
        oversized,
        limits=DiscoveryLimits(maximum_package_members=2, maximum_uncompressed_bytes=1024),
    )
    assert not candidate.valid
    assert any("limit exceeded" in error for error in candidate.errors)


def test_depth_and_candidate_limits_are_enforced(tmp_path: Path) -> None:
    at_limit = tmp_path.joinpath(*(f"d{index}" for index in range(12))) / "package.zip"
    write_synthetic_package(at_limit, stage="diagnostic")
    assert discover_packages((tmp_path,), requirement=_requirement()).selected is not None
    no_match = discover_packages(
        (tmp_path,),
        requirement=_requirement(),
        limits=DiscoveryLimits(maximum_depth=11),
    )
    assert no_match.status is SelectionStatus.NO_MATCHING_PACKAGE
    write_synthetic_package(tmp_path / "second.zip", stage="preflight")
    with pytest.raises(RuntimeError, match="candidate-count"):
        discover_packages((tmp_path,), limits=DiscoveryLimits(maximum_candidates=1))


def test_four_account_matrix_preserves_scientific_identity(tmp_path: Path) -> None:
    rows = run_four_account_matrix(tmp_path)
    assert len(rows) == 36
    assert all(row["result"] == "PASS" for row in rows)
    assert FIXTURE_LABELS == {
        "synthetic_validation_only": True,
        "not_real_kaggle_input": True,
        "not_real_kaggle_output": True,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    by_stage: dict[str, set[str]] = {}
    for row in rows:
        by_stage.setdefault(str(row["stage"]), set()).add(str(row["selected_identity"]))
    assert all(len(identities) == 1 for identities in by_stage.values())
    closure_rows = [row for row in rows if row["stage"] == "builder_faithful_rehearsal"]
    assert len(closure_rows) == 4
    assert all(row["dependency_status"] == "27_BUILDER_STAGES_WITH_REAL_IMPORTERS" for row in closure_rows)


def _asset_manifest(root: Path, *, asset_id: str = "clip__asset", revision: str = "rev-1") -> None:
    payload = root / "nested" / "weights.bin"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"synthetic asset")
    manifest = {
        "schema_version": "certgen.synthetic_asset_manifest.v1",
        "files": [
            {
                "path": "nested/weights.bin",
                "size": payload.stat().st_size,
                "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
                "asset_id": asset_id,
                "revision": revision,
                "license_status": "synthetic_fixture_only",
            }
        ],
        **FIXTURE_LABELS,
    }
    (root / "asset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_asset_mount_identity_and_hash_are_path_agnostic(tmp_path: Path) -> None:
    correct = tmp_path / "random-model-dataset" / "deep"
    _asset_manifest(correct)
    _asset_manifest(tmp_path / "unrelated", asset_id="other__asset")
    result = discover_asset_mount((tmp_path,), required_assets={"clip__asset": "rev-1"})
    assert result["status"] == "SELECTED_UNIQUE_VALID_ASSET_MOUNT"
    assert Path(result["selected"]["root"]) == correct
    (correct / "nested/weights.bin").write_bytes(b"corrupt")
    assert discover_asset_mount((tmp_path,), required_assets={"clip__asset": "rev-1"})["status"] == "NO_MATCHING_ASSET_MOUNT"


def _compatible_versions(profile: str) -> dict[str, str]:
    candidates = [
        "0.5.3", "0.22.1", "0.34.0", "0.34.3", "1.8.1", "1.15.3", "1.7.1", "2.0.2",
        "2.7.1", "4.53.2", "6.0.2", "11.2.1", "25.0",
    ]
    values: dict[str, str] = {}
    for raw in COMPATIBILITY_PROFILES[profile]:
        requirement = Requirement(raw)
        values[requirement.name] = next(value for value in candidates if value in requirement.specifier)
    return values


def _fake_pip(returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["python", "-m", "pip", "check"], returncode, stdout="ok\n", stderr="")


def _wheelhouse(root: Path, profile: str, *, omit: str | None = None) -> None:
    requirements_root = Path(__file__).parents[1] / "requirements"
    lock_names = {
        "kaggle_t4x2_diagnostic": "kaggle-diagnostic.lock",
        "kaggle_t4x2_preflight": "kaggle-preflight.lock",
        "kaggle_t4x2_generation": "kaggle-generation.lock",
        "kaggle_t4x2_features": "kaggle-features.lock",
    }
    requirements = _lock_requirements(requirements_root / lock_names[profile])
    files = []
    root.mkdir(parents=True)
    for raw in requirements:
        name = Requirement(raw).name
        if name == omit:
            continue
        filename = f"{name.replace('-', '_')}-1.0-py3-none-any.whl"
        wheel = root / filename
        wheel.write_bytes(f"synthetic wheel placeholder for {name}".encode())
        files.append(
            {
                "path": filename,
                "size": wheel.stat().st_size,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "certgen.wheelhouse_manifest.v1",
        "profiles": [profile],
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "platforms": ["any"],
        "files": files,
        **FIXTURE_LABELS,
    }
    (root / "wheelhouse_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_dependency_profiles_and_three_modes_are_closed(tmp_path: Path) -> None:
    assert "kaggle_t4x2_diagnostic" in COMPATIBILITY_PROFILES
    joined = "\n".join(raw for rows in COMPATIBILITY_PROFILES.values() for raw in rows).casefold()
    assert "timm" not in joined and "open-clip" not in joined

    profile = "kaggle_t4x2_generation"
    versions = _compatible_versions(profile)
    preinstalled = bootstrap_environment(
        profile,
        output_dir=tmp_path / "preinstalled",
        network_allowed=False,
        apply=True,
        install_mode="USE_PREINSTALLED_VALIDATED",
        version_getter=versions.get,
        pip_checker=lambda *args, **kwargs: _fake_pip(),
        importer=lambda name: object(),
    )
    assert preinstalled["status"] == "ENVIRONMENT_COMPATIBLE"
    assert isinstance(preinstalled["import_smoke_test"], dict)
    assert preinstalled["import_smoke_test"]["passed"] is True

    installed: dict[str, str] = {}

    def online_install(*args, **kwargs):  # type: ignore[no-untyped-def]
        installed.update(versions)
        return subprocess.CompletedProcess(args[0], 0, stdout="installed", stderr="")

    online = bootstrap_environment(
        profile,
        output_dir=tmp_path / "online",
        network_allowed=True,
        apply=True,
        install_mode="KAGGLE_INTERNET_ON_INSTALL",
        version_getter=installed.get,
        installer=online_install,
        pip_checker=lambda *args, **kwargs: _fake_pip(),
    )
    assert online["status"] == "KERNEL_RESTART_REQUIRED"

    wheelhouse = tmp_path / "arbitrary-wheelhouse-mount" / "deep"
    _wheelhouse(wheelhouse, profile)
    offline_versions: dict[str, str] = {}

    def offline_install(command, **kwargs):  # type: ignore[no-untyped-def]
        assert "--no-index" in command and "--find-links" in command and "-r" in command and "-c" in command
        offline_versions.update(versions)
        return subprocess.CompletedProcess(command, 0, stdout="installed offline", stderr="")

    offline = bootstrap_environment(
        profile,
        output_dir=tmp_path / "offline",
        network_allowed=False,
        apply=True,
        install_mode="PRIVATE_WHEELHOUSE_OFFLINE",
        search_roots=(tmp_path,),
        version_getter=offline_versions.get,
        installer=offline_install,
        pip_checker=lambda *args, **kwargs: _fake_pip(),
    )
    assert offline["status"] == "KERNEL_RESTART_REQUIRED"
    assert offline["resolved_wheelhouse"] == str(wheelhouse)


def test_wheelhouse_missing_distribution_pip_check_and_import_smoke_fail_closed(tmp_path: Path) -> None:
    profile = "kaggle_t4x2_diagnostic"
    missing = tmp_path / "missing-wheel"
    _wheelhouse(missing, profile, omit="torch")
    assert discover_wheelhouse((tmp_path,), profile=profile)["status"] == "NO_MATCHING_WHEELHOUSE"
    versions = _compatible_versions(profile)
    with pytest.raises(RuntimeError, match="pip check"):
        bootstrap_environment(
            profile,
            output_dir=tmp_path / "pip-failure",
            network_allowed=False,
            apply=True,
            install_mode="USE_PREINSTALLED_VALIDATED",
            version_getter=versions.get,
            pip_checker=lambda *args, **kwargs: _fake_pip(1),
            importer=lambda name: object(),
        )
    with pytest.raises(RuntimeError, match="import smoke"):
        bootstrap_environment(
            profile,
            output_dir=tmp_path / "import-failure",
            network_allowed=False,
            apply=True,
            install_mode="USE_PREINSTALLED_VALIDATED",
            version_getter=versions.get,
            pip_checker=lambda *args, **kwargs: _fake_pip(),
            importer=lambda name: (_ for _ in ()).throw(ImportError("synthetic failure")),
        )
