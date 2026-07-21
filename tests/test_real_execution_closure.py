from __future__ import annotations

import hashlib
import json
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.model_adapters import TextToImageAdapter, UnsupportedModelAdapter, adapter_for_model
from certgen.cvpr.output_schemas import expected_output_schema, validate_output_zip
from certgen.cvpr.prepare import prepare_family, prepare_preflight
from certgen.cvpr.synthetic_runtime import run_synthetic_runtime
from certgen.notebooks.final_zip import finalize_output_zip
from certgen.notebooks.network_policy import NetworkMode, NetworkPolicy, network_policy_from_config
from certgen.notebooks.subprocess_orchestrator import WorkerSpec, run_workers
from certgen.packaging.v9_import_repair import _run_id_from_archive


class _Generator:
    def __init__(self, device: str) -> None:
        self.device = device

    def manual_seed(self, seed: int) -> "_Generator":
        self.seed = seed
        return self


class _Torch:
    float16 = "float16"
    float32 = "float32"
    bfloat16 = "bfloat16"
    Generator = _Generator
    cuda = SimpleNamespace(empty_cache=lambda: None)


class _Pipeline:
    def __init__(self) -> None:
        self.scheduler = SimpleNamespace()
        self.calls: list[dict[str, Any]] = []

    def to(self, device: str) -> "_Pipeline":
        self.device = device
        return self

    def __call__(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        from PIL import Image

        return SimpleNamespace(images=[Image.new("RGB", (16, 12)) for _ in kwargs["generator"]])


def _runtime() -> dict[str, Any]:
    return {
        "batch_size": 2,
        "seeds": [4, 7],
        "num_inference_steps": 9,
        "scheduler": "checkpoint_default_pinned",
        "guidance_scale": 3.5,
        "width": 16,
        "height": 12,
        "prompts": ["a", "b"],
        "class_ids": [],
        "precision": "float16",
        "output_type": "pil",
    }


def test_text_adapter_applies_every_frozen_generation_parameter(tmp_path: Path) -> None:
    pipeline = _Pipeline()
    observed_loader: dict[str, Any] = {}

    def loader(path: str, **kwargs: Any) -> _Pipeline:
        observed_loader.update(path=path, **kwargs)
        return pipeline

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    adapter = TextToImageAdapter(loader=loader, torch_module=_Torch())
    adapter.load(snapshot, _runtime(), "cuda:0")
    images = adapter.generate_batch(_runtime())
    assert len(images) == 2
    assert observed_loader == {"path": str(snapshot), "local_files_only": True, "torch_dtype": "float16"}
    assert len(pipeline.calls) == 1
    assert {key: value for key, value in pipeline.calls[0].items() if key != "generator"} == {
        "num_inference_steps": 9,
        "output_type": "pil",
        "width": 16,
        "height": 12,
        "prompt": ["a", "b"],
        "guidance_scale": 3.5,
    }
    assert [generator.seed for generator in pipeline.calls[0]["generator"]] == [4, 7]
    assert adapter.applied_record and adapter.applied_record["differences"] == {}


def test_unsupported_cfm_and_unknown_adapters_fail_before_packaging() -> None:
    cfm = adapter_for_model({"model_id": "cfm", "family": "flow_matching", "adapter": "generic"})
    assert isinstance(cfm, UnsupportedModelAdapter)
    with pytest.raises(NotImplementedError, match="CFM remains blocked"):
        cfm.validate_config(_runtime())
    unknown = adapter_for_model({"model_id": "mystery", "family": "other", "conditioning": "unconditional"})
    assert isinstance(unknown, UnsupportedModelAdapter)


def test_network_modes_separate_dependencies_and_assets(tmp_path: Path) -> None:
    normal = NetworkPolicy(NetworkMode.ONLINE_DEPENDENCIES_OFFLINE_ASSETS, True, False)
    normal.validate()
    parsed = network_policy_from_config(normal.as_dict())
    assert parsed.model_asset_network_allowed is False
    with pytest.raises(ValueError, match="contradict"):
        NetworkPolicy(NetworkMode.OFFLINE_DEPENDENCIES_OFFLINE_ASSETS, True, False).validate()
    with pytest.raises(FileNotFoundError, match="wheelhouse"):
        NetworkPolicy(NetworkMode.OFFLINE_DEPENDENCIES_OFFLINE_ASSETS, False, False, str(tmp_path)).validate()


def _spec(tmp_path: Path, worker: int, gpu: int, *, fail: bool = False, sleep: float = 0.02) -> WorkerSpec:
    marker = tmp_path / f"worker-{worker}.json"
    args = ["--out", str(marker), "--sleep", str(sleep)]
    if fail:
        args.append("--fail")
    return WorkerSpec(f"worker-{worker}", "certgen.notebooks.workers.fake_worker", gpu, f"shard-{worker}", tuple(args), str(marker))


def test_per_gpu_queues_are_serial_failure_isolated_and_resume_is_hash_checked(tmp_path: Path) -> None:
    specs = [_spec(tmp_path, index, index % 2, sleep=0.04) for index in range(6)]
    started = time.monotonic()
    result = run_workers(specs, output_dir=tmp_path / "queues", timeout_seconds=10)
    duration = time.monotonic() - started
    assert result["status"] == "COMPLETE"
    assert duration >= 0.10  # three jobs per GPU serialize; the two GPU queues overlap.
    rows = json.loads((tmp_path / "queues" / "worker_schedule.json").read_text(encoding="utf-8"))["workers"]
    assert {row["physical_gpu"] for row in rows} == {0, 1}

    (tmp_path / "worker-0_artifact.json").write_text("corrupt\n", encoding="utf-8")
    resumed = run_workers(specs[:1], output_dir=tmp_path / "resume", resume=True, timeout_seconds=10)
    assert resumed["workers"][0]["status"] == "COMPLETE"
    assert resumed["workers"][0]["resume_status"] == "RERUN_INVALID_COMPLETION"
    assert (tmp_path / "resume" / "quarantine" / "worker-0" / "quarantine_record.json").is_file()

    failure_specs = [_spec(tmp_path / "failed", 0, 0, fail=True), _spec(tmp_path / "failed", 1, 0), _spec(tmp_path / "failed", 2, 1)]
    failed = run_workers(failure_specs, output_dir=tmp_path / "failure", timeout_seconds=10)
    statuses = {row["worker_id"]: row["status"] for row in failed["workers"]}
    assert statuses == {"worker-0": "FAILED", "worker-1": "CANCELLED_QUEUE_FAILURE", "worker-2": "COMPLETE"}


def test_resume_marker_rejects_output_path_traversal(tmp_path: Path) -> None:
    spec = _spec(tmp_path, 0, 0)
    assert run_workers([spec], output_dir=tmp_path / "first")["status"] == "COMPLETE"
    marker = Path(spec.completion_marker or "")
    payload = json.loads(marker.read_text(encoding="utf-8"))
    outside = tmp_path.parent / "outside-resume-fixture.json"
    outside.write_text("outside\n", encoding="utf-8")
    payload["outputs"] = {"../outside-resume-fixture.json": file_sha256(outside)}
    marker.write_text(json.dumps(payload), encoding="utf-8")
    resumed = run_workers([spec], output_dir=tmp_path / "second", resume=True)
    assert resumed["workers"][0]["resume_status"] == "RERUN_INVALID_COMPLETION"
    assert "unsafe completion output path" in resumed["workers"][0]["resume_reason"]


def test_output_schema_rejects_unknown_roots_and_accepts_canonical_layout(tmp_path: Path) -> None:
    schema = expected_output_schema("generation")
    config = {
        "kind": "generation",
        "run_id": "fixture-generation-run",
        "claim_allowed": False,
    }
    config["configuration_hash"] = stable_hash_json(config)
    status = {
        "status_code": "GENERATION_COMPLETE",
        "output_schema_version": schema["schema_version"],
        "configuration_hash": config["configuration_hash"],
        "expected_workers": ["m__s"],
        "completed_workers": ["m__s"],
        "claim_allowed": False,
    }
    files = {
        "configuration.yaml": yaml.safe_dump(config, sort_keys=False),
        "run_identity.json": json.dumps(
            {
                "run_id": config["run_id"],
                "configuration_hash": config["configuration_hash"],
                "input_manifest_hash": "i" * 64,
                "asset_manifest_hash": "a" * 64,
                "claim_allowed": False,
            }
        ),
        "generation_status.json": json.dumps(status),
        "per_model/m/status.json": "{}",
        "model_cache/inception/inception_v3_google-0cc3c7bd.pth": "fixture-weights",
    }
    integrity = {
        "files": [
            {
                "path": name,
                "size": len(data.encode("utf-8")),
                "sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
            }
            for name, data in files.items()
        ],
        "claim_allowed": False,
    }
    valid = tmp_path / "valid.zip"
    with zipfile.ZipFile(valid, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr("integrity_manifest.json", json.dumps(integrity))
    assert validate_output_zip("generation", str(valid))["passed"]
    invalid = tmp_path / "invalid.zip"
    with zipfile.ZipFile(invalid, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr("integrity_manifest.json", json.dumps(integrity))
        archive.writestr("unexpected/private.txt", "bad")
    verdict = validate_output_zip("generation", str(invalid))
    assert not verdict["passed"] and any("unsupported" in error for error in verdict["errors"])


def test_final_zip_reuses_valid_and_rebuilds_corrupt_archive(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "status.json").write_text("{}\n", encoding="utf-8")
    cache_metadata = run / "model_cache" / "fixture" / ".cache" / "download.lock"
    cache_metadata.parent.mkdir(parents=True)
    cache_metadata.write_text("transient\n", encoding="utf-8")
    archive = tmp_path / "final.zip"
    first = finalize_output_zip(run, archive, mode="resume", configuration_hash="c" * 64, asset_manifest_hash="a" * 64)
    assert first["status"] == "REBUILT_FINAL_ZIP"
    with zipfile.ZipFile(archive) as built:
        assert not any(".cache" in Path(name).parts for name in built.namelist())
    second = finalize_output_zip(run, archive, mode="resume", configuration_hash="c" * 64, asset_manifest_hash="a" * 64)
    assert second["status"] == "REUSED_VALID_FINAL_ZIP"
    archive.write_bytes(b"corrupt")
    third = finalize_output_zip(run, archive, mode="resume", configuration_hash="c" * 64, asset_manifest_hash="a" * 64)
    assert third["status"] == "REBUILT_FINAL_ZIP"
    assert file_sha256(archive) == third["archive_sha256"]


def test_import_default_name_preserves_canonical_run_identity(tmp_path: Path) -> None:
    archive = tmp_path / "identity.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr(
            "run_identity.json",
            json.dumps({"run_id": "canonical-stage-run", "claim_allowed": False}),
        )
    assert _run_id_from_archive(archive, "generation", "a" * 64) == "canonical-stage-run"


def test_preflight_builder_includes_models_extractors_capabilities_and_schema(tmp_path: Path) -> None:
    model_registry = tmp_path / "models.yaml"
    model_registry.write_text(
        "models:\n- model_id: fixture_ddpm\n  benchmark_id: cifar10\n  family: DDPM\n  conditioning: unconditional\n  adapter: diffusers_DDPMPipeline\n  checkpoint_or_sample_source: fixture/model\n  revision: fixture-v1\n  resolution: 32x32\n  license: fixture_approved\n",
        encoding="utf-8",
    )
    expected = {
        "extractor_id": "fixture", "model_identifier": "fixture/extractor", "revision": "fixture-v1", "processor_class": "FixtureProcessor",
        "input_resolution": 8, "resize_size": 8, "crop_size": 8, "crop_mode": "none", "interpolation": "nearest", "antialias": True,
        "pixel_range": "0..1", "channel_order": "RGB", "mean": [0, 0, 0], "std": [1, 1, 1], "feature_normalization": "none",
        "precision": "float32", "output_dimension": 7, "package_versions": {"fixture": "1"},
    }
    feature_registry = tmp_path / "features.yaml"
    feature_registry.write_text(
        "feature_spaces:\n- feature_space_id: fixture\n  model_identifier: fixture/extractor\n  revision: fixture-v1\n  expected_dimension: 7\n  license: fixture_approved\n  expected_preprocessing:\n"
        + "".join(f"    {key}: {json.dumps(value)}\n" for key, value in expected.items()),
        encoding="utf-8",
    )
    benchmark_registry = tmp_path / "benchmarks.yaml"
    benchmark_registry.write_text("benchmarks:\n- benchmark_id: cifar10\n", encoding="utf-8")
    result = prepare_preflight(out_dir=tmp_path / "prepared", policy="ONLINE_PREFLIGHT_DOWNLOAD", model_registry=model_registry, feature_registry=feature_registry, benchmark_registry=benchmark_registry)
    assert result["status"] == "PREFLIGHT_PACKAGE_READY"
    with zipfile.ZipFile(result["package"]["zip_path"]) as archive:
        names = set(archive.namelist())
    assert {"preflight_config.yaml", "models.yaml", "extractors.yaml", "adapter_capabilities.yaml", "dependency_profile.yaml", "expected_output_schema.json", "run_identity.json", "KAGGLE_INSTRUCTIONS.md"} <= names
    assert any(name.startswith("worker_configs/") for name in names)


def test_family_builder_uses_actual_registry_fields_and_full_cartesian_product(tmp_path: Path) -> None:
    registry = tmp_path / "comparisons.csv"
    registry.write_text(
        "comparison_id,benchmark_id,model_a,model_b,prospective_or_posthoc,feature_spaces,metrics,sample_budgets,family_id,status\n"
        "a_vs_b,cifar10,a,b,prospective,inception|clip,rbf_mmd,1000|10000,family,registered\n",
        encoding="utf-8",
    )
    family = prepare_family(out_dir=tmp_path / "family", comparison_registry=registry, alpha=0.04)
    assert family["number_of_hypotheses"] == 4
    assert family["alpha_per_hypothesis"] == pytest.approx(0.01)
    posthoc = tmp_path / "posthoc.csv"
    posthoc.write_text(registry.read_text(encoding="utf-8").replace("prospective", "posthoc"), encoding="utf-8")
    blocked = prepare_family(out_dir=tmp_path / "blocked", comparison_registry=posthoc)
    assert blocked["status"] == "BLOCKED_NO_FROZEN_COMPARISONS"


def test_synthetic_real_contract_uses_all_21_stages(tmp_path: Path) -> None:
    result = run_synthetic_runtime(tmp_path / "synthetic")
    assert result["status"] == "synthetic_real_contract_passed"
    assert result["stage_count"] == 21
    assert list(result["stages"])[0].startswith("01_")
    assert list(result["stages"])[-1].startswith("21_")
