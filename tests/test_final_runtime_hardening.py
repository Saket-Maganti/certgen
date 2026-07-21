from __future__ import annotations

import json
import hashlib
import subprocess
import zipfile
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from certgen.notebooks.environment_bootstrap import (
    COMPATIBILITY_PROFILES,
    bootstrap_environment,
    inspect_profile,
    installation_plan,
)
from certgen.cvpr.fingerprint import (
    REQUIRED_INPUTS,
    build_reproducibility_fingerprint,
    verify_reproducibility_fingerprint,
)
from certgen.notebooks.kaggle_io import disk_guard
from certgen.notebooks.generation_runtime import (
    FixtureBatchAdapter,
    GenerationSample,
    GenerationSettings,
    generate_batches,
)
from certgen.notebooks.model_assets import (
    AssetPolicy,
    AssetRequirement,
    inventory_cache,
    validate_asset_manifest,
    validate_asset_identity,
    validate_policy_preconditions,
)
from certgen.notebooks.preprocessing_contract import (
    PreprocessingContract,
    compare_preprocessing,
)
from certgen.notebooks.run_state import RunIdentity, RunMode, prepare_run_directory
from certgen.notebooks.subprocess_orchestrator import WorkerSpec, run_workers
from certgen.release.archive import build_archive
from certgen.packaging.v9_import_repair import import_repair


def _versions(profile: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in COMPATIBILITY_PROFILES[profile]:
        requirement = Requirement(raw)
        candidates = ["0.22.1", "0.34.0", "0.33.0", "0.5.3", "1.0.16", "1.8.1", "1.13.0", "1.5.0", "2.0.2", "2.7.1", "2.32.0", "4.53.2", "11.2.1"]
        values[requirement.name] = next(candidate for candidate in candidates if candidate in requirement.specifier)
    return values


def test_environment_bootstrap_profiles_plan_only_incompatible_packages(tmp_path: Path) -> None:
    profile = "kaggle_t4x2_generation"
    versions = _versions(profile)
    compatible = inspect_profile(profile, version_getter=versions.get)
    assert installation_plan(compatible) == []
    missing_name = Requirement(COMPATIBILITY_PROFILES[profile][0]).name
    versions.pop(missing_name)
    plan = installation_plan(inspect_profile(profile, version_getter=versions.get))
    assert any(Requirement(raw).name == missing_name for raw in plan)
    with pytest.raises(RuntimeError, match="offline bootstrap"):
        bootstrap_environment(profile, output_dir=tmp_path / "offline", network_allowed=False, apply=True, version_getter=versions.get)


def test_environment_bootstrap_install_failure_restart_and_revalidation(tmp_path: Path) -> None:
    profile = "kaggle_t4x2_generation"
    versions: dict[str, str] = {}

    def failure(*args, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(args[0], 9, stdout="pip stdout", stderr="pip failed")

    with pytest.raises(RuntimeError, match="installation failed"):
        bootstrap_environment(profile, output_dir=tmp_path / "failure", network_allowed=True, apply=True, version_getter=versions.get, installer=failure)
    assert "pip failed" in (tmp_path / "failure" / "pip_install.log").read_text(encoding="utf-8")

    def success(*args, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(args[0], 0, stdout="installed", stderr="")

    restart = bootstrap_environment(profile, output_dir=tmp_path / "restart", network_allowed=True, apply=True, version_getter=versions.get, installer=success)
    assert restart["status"] == "KERNEL_RESTART_REQUIRED"
    assert restart["restart_required"] is True
    with pytest.raises(RuntimeError, match="failed closed"):
        bootstrap_environment(profile, output_dir=tmp_path / "revalidate", network_allowed=True, apply=True, revalidate_after_restart=True, version_getter=versions.get, installer=success)


def test_asset_policy_online_and_offline_cache_fail_closed(tmp_path: Path) -> None:
    requirement = AssetRequirement("asset", "model", "rev-1", "fixture/source", "verified_fixture", False, ("config.json", "weights/model.bin"))
    cache = tmp_path / "cache"
    (cache / "weights").mkdir(parents=True)
    (cache / "config.json").write_text("{}", encoding="utf-8")
    (cache / "weights" / "model.bin").write_bytes(b"fixture")
    validate_policy_preconditions(requirement, policy=AssetPolicy.OFFLINE_PACKAGED_CACHE, internet_enabled=False, token_present=False, cache_root=cache)
    with pytest.raises(RuntimeError, match="internet disabled"):
        validate_policy_preconditions(requirement, policy=AssetPolicy.OFFLINE_PACKAGED_CACHE, internet_enabled=True, token_present=False, cache_root=cache)
    with pytest.raises(RuntimeError, match="internet"):
        validate_policy_preconditions(requirement, policy=AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD, internet_enabled=False, token_present=False, cache_root=cache)
    manifest = inventory_cache(requirement, cache, AssetPolicy.OFFLINE_PACKAGED_CACHE)
    validate_asset_manifest(manifest, cache_root=cache)
    (cache / "weights" / "model.bin").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_asset_manifest(manifest, cache_root=cache)


def _fake_specs(tmp_path: Path, *, fail_second: bool = False, sleep: float = 0.0) -> list[WorkerSpec]:
    specs = []
    for index in range(2):
        args = ["--out", str(tmp_path / f"worker-{index}.json")]
        if fail_second and index == 1:
            args.append("--fail")
        if sleep:
            args.extend(["--sleep", str(sleep)])
        specs.append(WorkerSpec(f"worker-{index}", "certgen.notebooks.workers.fake_worker", index, f"shard-{index}", tuple(args), str(tmp_path / f"worker-{index}.json")))
    return specs


def test_subprocess_workers_pin_devices_preserve_logs_failures_timeouts_and_resume(tmp_path: Path) -> None:
    success = run_workers(_fake_specs(tmp_path), output_dir=tmp_path / "success", timeout_seconds=10)
    assert success["status"] == "COMPLETE"
    payloads = [json.loads((tmp_path / f"worker-{index}.json").read_text(encoding="utf-8")) for index in range(2)]
    assert [row["cuda_visible_devices"] for row in payloads] == ["0", "1"]
    assert all(Path(row["log"]).is_file() for row in success["workers"])
    resumed = run_workers(_fake_specs(tmp_path), output_dir=tmp_path / "resumed", resume=True)
    assert all(row["status"] == "REUSED_VALID_COMPLETION" for row in resumed["workers"])

    failed_root = tmp_path / "failed-workers"
    failure = run_workers(_fake_specs(failed_root, fail_second=True), output_dir=tmp_path / "failure", timeout_seconds=10)
    assert failure["status"] == "PARTIAL_FAILURE"
    assert any(row["exit_code"] == 7 for row in failure["workers"])
    timeout_root = tmp_path / "timeout-workers"
    timeout = run_workers(_fake_specs(timeout_root, sleep=1.0), output_dir=tmp_path / "timeout", timeout_seconds=0.05)
    assert timeout["status"] == "PARTIAL_FAILURE"
    assert any(row["status"] == "TIMEOUT" for row in timeout["workers"])


def test_batched_generation_oom_atomic_resume_and_identity_checks(tmp_path: Path) -> None:
    samples = [GenerationSample(f"sample-{index}", index) for index in range(7)]
    adapter = FixtureBatchAdapter(size=(8, 8), oom_above=2)
    settings = GenerationSettings("fixture", "fixture", 1, None, "float32", "cpu", 4, image_size=(8, 8))
    first = generate_batches(adapter=adapter, samples=samples, settings=settings, output_root=tmp_path / "generated", configuration_hash="a" * 64, resume=False)
    assert first["total_samples"] == 7
    assert first["effective_batch_size"] == 2
    assert first["OOM_events"] == 1
    second = generate_batches(adapter=adapter, samples=samples, settings=settings, output_root=tmp_path / "generated", configuration_hash="a" * 64, resume=True)
    assert second["generated_now"] == 0
    assert second["completed_before_resume"] == 7
    with pytest.raises(ValueError, match="conflicting batch manifest"):
        generate_batches(adapter=adapter, samples=samples, settings=settings, output_root=tmp_path / "generated", configuration_hash="b" * 64, resume=True)
    with pytest.raises(ValueError, match="duplicate seeds"):
        generate_batches(adapter=adapter, samples=[GenerationSample("x", 1), GenerationSample("y", 1)], settings=settings, output_root=tmp_path / "duplicate", configuration_hash="c" * 64, resume=False)


def _preprocessing(mean: tuple[float, ...] = (0.5, 0.5, 0.5)) -> PreprocessingContract:
    return PreprocessingContract("fixture", "fixture/model", "rev-1", "FixtureProcessor", 8, 8, 8, "none", "nearest", True, "0..1", "RGB", mean, (0.5, 0.5, 0.5), "l2", "float32", 6, {"fixture": "1.0"})


def test_observed_preprocessing_contract_matches_and_reports_difference(tmp_path: Path) -> None:
    result = compare_preprocessing(_preprocessing(), _preprocessing(), difference_report=tmp_path / "match.json")
    assert result["status"] == "MATCH"
    with pytest.raises(ValueError, match="differs"):
        compare_preprocessing(_preprocessing(), _preprocessing((0.4, 0.5, 0.5)), difference_report=tmp_path / "mismatch.json")
    mismatch = json.loads((tmp_path / "mismatch.json").read_text(encoding="utf-8"))
    assert "mean" in mismatch["differences"]


def test_run_modes_resume_restart_force_new_and_hash_mismatch(tmp_path: Path) -> None:
    identity = RunIdentity("run", "c" * 64, "i" * 64, "a" * 64)
    created = prepare_run_directory(tmp_path, identity, RunMode.FORCE_NEW_RUN)
    force_root = Path(created["run_dir"])
    assert force_root.name.startswith("run__")
    base = tmp_path / "resume-root"
    prepare_run_directory(base, identity, RunMode.RESTART)
    resumed = prepare_run_directory(base, identity, RunMode.RESUME)
    assert resumed["run_id"] == "run"
    with pytest.raises(ValueError, match="identity mismatch"):
        prepare_run_directory(base, RunIdentity("run", "x" * 64, "i" * 64, "a" * 64), RunMode.RESUME)
    restarted = prepare_run_directory(base, identity, RunMode.RESTART)
    assert restarted["quarantined"]


def test_clean_archive_preserves_paths_and_excludes_metadata(tmp_path: Path) -> None:
    payload = build_archive(output=tmp_path / "certgen.zip", run_tests=False)
    assert payload["status"] == "ARCHIVE_VERIFIED"
    names = {row["path"] for row in payload["manifest"]}
    assert "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb" in names
    assert not any("__pycache__" in name or name.endswith(".pyc") or "__MACOSX" in name for name in names)


def test_disk_guard_and_complete_reproducibility_fingerprint_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="insufficient disk"):
        disk_guard(tmp_path, 10**30, safety_margin_bytes=0)

    paths: dict[str, Path] = {}
    for index, name in enumerate(REQUIRED_INPUTS):
        path = tmp_path / f"{index:02d}-{name}.json"
        path.write_text(json.dumps({"name": name}), encoding="utf-8")
        paths[name] = path
    payload = build_reproducibility_fingerprint(
        paths,
        environment={"python": "fixture", "torch": "not-loaded"},
        root=tmp_path,
        out=tmp_path / "fingerprint.json",
    )
    assert payload["complete"] is True
    assert verify_reproducibility_fingerprint(payload, root=tmp_path)["passed"] is True
    paths["generation_config"].write_text("changed", encoding="utf-8")
    verdict = verify_reproducibility_fingerprint(payload, root=tmp_path)
    assert verdict["passed"] is False
    assert "fingerprint input changed: generation_config" in verdict["errors"]
    with pytest.raises(ValueError, match="keys mismatch"):
        build_reproducibility_fingerprint(
            {name: path for name, path in paths.items() if name != "asset_manifest"},
            environment={"python": "fixture"},
            root=tmp_path,
        )


def test_failure_injection_corrupt_image_wrong_revision_missing_shard_and_zip_hash(tmp_path: Path) -> None:
    class CorruptImage:
        mode = "RGB"
        size = (8, 8)

        def save(self, path: Path, *, format: str) -> None:  # noqa: A002
            assert format == "PNG"
            Path(path).write_bytes(b"not-a-png")

    class CorruptAdapter:
        supports_generator_list = True

        def generate(self, *, seeds, prompts):  # type: ignore[no-untyped-def]
            return [CorruptImage() for _ in seeds]

        def clear_cache(self) -> None:
            return None

    with pytest.raises(Exception, match="cannot identify image file"):
        generate_batches(
            adapter=CorruptAdapter(),  # type: ignore[arg-type]
            samples=[GenerationSample("bad-image", 1)],
            settings=GenerationSettings("fixture", "fixture", 1, None, "float32", "cpu", 1, image_size=(8, 8)),
            output_root=tmp_path / "corrupt-image",
            configuration_hash="z" * 64,
            resume=False,
        )

    with pytest.raises(ValueError, match="configured model/revision"):
        validate_asset_identity(
            {"model_or_extractor_id": "model-a", "revision": "rev-old"},
            model_or_extractor_id="model-a",
            revision="rev-new",
        )

    files: dict[str, bytes] = {
        "generation_status.json": json.dumps({"status_code": "GENERATION_COMPLETE", "passed": True, "expected_workers": ["model-a__shard_0000", "model-a__shard_0001"], "claim_allowed": False}).encode(),
        "per_model/model-a/per_shard/shard_0000/status.json": json.dumps({"status_code": "SHARD_COMPLETE", "claim_allowed": False}).encode(),
        "per_model/model-a/per_shard/shard_0000/manifest.jsonl": b'{"sample_id":"one","seed":1,"claim_allowed":false}\n',
        "copyback_instructions.md": b"not paper evidence; claim_allowed=false\n",
    }
    integrity = {
        "files": [
            {"path": name, "size": len(data), "sha256": "0" * 64 if name.endswith("manifest.jsonl") else hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ],
        "claim_allowed": False,
    }
    archive = tmp_path / "corrupt-generation.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for name, data in files.items():
            handle.writestr(name, data)
        handle.writestr("integrity_manifest.json", json.dumps(integrity))
    imported = import_repair(
        kind="generation",
        zip_path=archive,
        out_dir=tmp_path / "rejected-import",
        out_json=tmp_path / "rejected.json",
        out_report=tmp_path / "rejected.md",
        registry_path=tmp_path / "registry.jsonl",
    )
    assert imported["passed"] is False
    assert any("integrity hash mismatch" in error for error in imported["errors"])
    assert any("missing expected workers" in error for error in imported["errors"])
