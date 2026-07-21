from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from PIL import Image

from certgen.__main__ import build_parser
from certgen.core.hashing import file_sha256
from certgen.cvpr.adapter_conformance import write_adapter_conformance_matrix
from certgen.cvpr.analysis import (
    compute_accounting_contract,
    point_vs_certified_contract,
    qualitative_gallery_contract,
    write_cross_feature_analysis,
    write_ranking_stability,
)
from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
from certgen.cvpr.contracts import configuration_hash
from certgen.cvpr.extractor_adapters import ClipImageExtractorAdapter, InceptionExtractorAdapter
from certgen.cvpr.image_manifest import read_image_manifest, write_image_manifest
from certgen.cvpr.prepare import prepare_family, prepare_preflight
from certgen.cvpr.readiness import readiness_report
from certgen.cvpr.registries import validate_preregistration
from certgen.cvpr.runtime_planner import (
    DERIVED_FROM_MEASURED_PREFLIGHT,
    MEASURED_PREFLIGHT,
    PLANNING_ESTIMATE,
    build_runtime_plan,
)
from certgen.cvpr.study import freeze_study
from certgen.notebooks.model_assets import AssetPolicy, AssetRequirement, inventory_cache


def test_minimal_profile_prepares_while_cfm_and_dino_remain_excluded(tmp_path: Path) -> None:
    result = prepare_preflight(
        out_dir=tmp_path / "minimal",
        policy=AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD,
        profile="cifar_integrity_minimal",
    )
    assert result["status"] == "PREFLIGHT_PACKAGE_READY"
    config = yaml.safe_load(Path(result["config"]).read_text(encoding="utf-8"))
    assert config["selected_models"] == [
        "google_ddpm_cifar10_candidate",
        "frank_ddpm_ema_cifar10_candidate",
    ]
    assert config["selected_extractors"] == ["inception", "clip"]
    assert "frank_cfm_cifar10_candidate" in config["registered_not_selected"]["models"]
    assert "dinov2" in config["registered_not_selected"]["extractors"]
    assert config["pilot_profile"]["claim_allowed"] is False

    cfm = prepare_preflight(
        out_dir=tmp_path / "cfm",
        policy=AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD,
        profile="cifar_full_candidate",
    )
    assert cfm["status"].startswith("BLOCKED")
    assert any("cfm" in blocker.lower() for blocker in cfm["blockers"])
    modern = prepare_preflight(
        out_dir=tmp_path / "modern",
        policy=AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD,
        profile="cifar_integrity_modern",
    )
    assert modern["status"].startswith("BLOCKED")
    assert any("dinov2" in blocker.lower() for blocker in modern["blockers"])


def test_study_freeze_is_profile_bound_and_cli_surface_exists(tmp_path: Path) -> None:
    result = freeze_study(
        "cifar_integrity_minimal", out_path=tmp_path / "study.yaml"
    )
    assert len(result["study_hash"]) == 64
    assert validate_preregistration(tmp_path / "study.yaml", require_frozen=True)["passed"]
    family = prepare_family(
        out_dir=tmp_path / "family",
        study_path=tmp_path / "study.yaml",
    )
    assert family["family_id"] == "cvpr_primary_cifar10"
    assert family["comparisons"] == ["checkpoint_variant"]
    assert family["number_of_hypotheses"] == 2
    assert family["controls_in_confirmatory_family"] is False
    assert family["study_hash"] == result["study_hash"]
    parser = build_parser()
    args = parser.parse_args(["freeze", "study", "--profile", "cifar_integrity_minimal"])
    assert args.freeze_kind == "study"
    runtime_args = parser.parse_args(["runtime-plan", "ingest-preflight", "report.json"])
    assert runtime_args.runtime_report == "report.json"


def test_canonical_image_manifest_rejects_legacy_and_tampering(tmp_path: Path) -> None:
    image = tmp_path / "images" / "one.png"
    image.parent.mkdir()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(image)
    row = {
        "sample_id": "sample-1",
        "role": "model",
        "model_id": "fixture-model",
        "relative_image_path": "images/one.png",
        "image_hash": file_sha256(image),
        "seed": 1,
        "prompt_or_class_id": None,
        "width": 8,
        "height": 8,
        "mode": "RGB",
        "source_run_id": "fixture-run",
        "source_manifest_hash": "a" * 64,
    }
    manifest = tmp_path / "manifest.jsonl"
    write_image_manifest([row], manifest, root=tmp_path, decode=True)
    assert read_image_manifest(manifest, root=tmp_path, decode=True)[0]["relative_image_path"] == "images/one.png"
    with pytest.raises(ValueError, match="legacy fields"):
        write_image_manifest([{**row, "path": "legacy.png"}], tmp_path / "legacy.jsonl")
    image.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        read_image_manifest(manifest, root=tmp_path, decode=True)


class _FakeModel:
    def __init__(self) -> None:
        self.fc = None
        self.loaded = False

    def load_state_dict(self, state: object) -> None:
        self.loaded = True

    def eval(self) -> "_FakeModel":
        return self

    def to(self, device: str) -> "_FakeModel":
        self.device = device
        return self


class _FakeTorch:
    class nn:
        class Identity:
            pass

    @staticmethod
    def load(path: str, *, map_location: str, weights_only: bool) -> dict[str, object]:
        assert Path(path).is_file()
        assert map_location == "cpu" and weights_only is True
        return {}


class _FakeModels:
    class Inception_V3_Weights:
        class IMAGENET1K_V1:
            @staticmethod
            def transforms() -> object:
                return object()

    @staticmethod
    def inception_v3(*, weights: object, aux_logits: bool) -> _FakeModel:
        assert weights is None and aux_logits is True
        return _FakeModel()


def test_inception_and_clip_load_exact_local_assets_without_network(tmp_path: Path) -> None:
    inception_cache = tmp_path / "inception"
    inception_cache.mkdir()
    (inception_cache / "weights.pth").write_bytes(b"fixture weights")
    manifest = inventory_cache(
        AssetRequirement(
            "inception__asset",
            "inception",
            "fixture-revision",
            "fixture/inception",
            "synthetic_fixture_only",
            False,
            ("weights.pth",),
        ),
        inception_cache,
        AssetPolicy.OFFLINE_PACKAGED_CACHE,
    )
    manifest.update(
        {
            "layout_type": "torchvision_local_weight_file",
            "loader_type": "torchvision_local_state_dict",
            "weight_enum": "Inception_V3_Weights.IMAGENET1K_V1",
            "weight_file": "weights.pth",
        }
    )
    adapter = InceptionExtractorAdapter(
        {
            "feature_space_id": "inception",
            "revision": "fixture-revision",
            "expected_preprocessing": {},
        },
        torch_module=_FakeTorch(),
        torchvision_models=_FakeModels(),
    )
    adapter.load(manifest, inception_cache, "cpu")
    assert adapter.model.loaded is True
    assert adapter.output_definition()["feature_definition"] == "final_global_average_pool_before_fc_2048d"

    calls: list[tuple[str, bool]] = []

    class _Loaded:
        def eval(self) -> "_Loaded":
            return self

        def to(self, device: str) -> "_Loaded":
            return self

    class _Factory:
        @staticmethod
        def from_pretrained(path: str, *, local_files_only: bool) -> _Loaded:
            calls.append((path, local_files_only))
            return _Loaded()

    clip_cache = tmp_path / "clip"
    clip_cache.mkdir()
    (clip_cache / "config.json").write_text("{}", encoding="utf-8")
    clip_manifest = inventory_cache(
        AssetRequirement("clip__asset", "clip", "clip-revision", "fixture/clip", "synthetic_fixture_only", False, ("config.json",)),
        clip_cache,
        AssetPolicy.OFFLINE_PACKAGED_CACHE,
    )
    transformers = SimpleNamespace(CLIPProcessor=_Factory, CLIPModel=_Factory)
    clip = ClipImageExtractorAdapter(
        {"feature_space_id": "clip", "revision": "clip-revision", "expected_preprocessing": {}},
        transformers_module=transformers,
    )
    clip.load(clip_manifest, clip_cache, "cpu")
    assert len(calls) == 2 and all(local_only for _, local_only in calls)
    assert clip.output_definition()["feature_definition"].startswith("projected_image_embedding")


def _certificate(comparison: str, feature: str, decision: str, budget: int = 1000) -> dict[str, object]:
    return {
        "comparison_id": comparison,
        "feature_space": feature,
        "decision": decision,
        "sample_budget": budget,
        "first_decision_n": 400 if decision in {"A_BETTER", "B_BETTER"} else None,
        "model_a": "a",
        "model_b": "b",
        "configuration_hash": "a" * 64,
        "family_configuration_hash": "b" * 64,
        "preprocessing_hash": "c" * 64,
        "reference_draw_hash": "d" * 64,
        "claim_allowed": False,
    }


def test_cross_feature_stability_and_value_contracts(tmp_path: Path) -> None:
    rows = [
        _certificate("a_vs_b", "inception", "A_BETTER"),
        _certificate("a_vs_b", "clip", "UNDECIDED_AT_BUDGET"),
        _certificate("c_vs_d", "inception", "A_BETTER"),
        _certificate("c_vs_d", "clip", "B_BETTER"),
    ]
    cross = write_cross_feature_analysis(rows, tmp_path / "cross")
    assert cross["direction_disagreements"] == 1
    assert (tmp_path / "cross" / "decided_in_one_unresolved_in_another.csv").is_file()
    stability_rows = [
        _certificate("a_vs_b", "inception", "UNDECIDED_AT_BUDGET", 1000),
        _certificate("a_vs_b", "inception", "A_BETTER", 10000),
    ]
    stability = write_ranking_stability(stability_rows, tmp_path / "stability")
    assert stability["partial_order_stability"][0]["edge_appearance_budget"] == 10000
    comparison = point_vs_certified_contract(
        point_estimates=[{"model_id": "b", "point_estimate": 2.0}, {"model_id": "a", "point_estimate": 1.0}],
        ranking={"directed_certified_edges": [], "unresolved_pairs": [{"model_a": "a", "model_b": "b"}]},
    )
    assert comparison["point_estimate_total_order"] == ["a", "b"]
    accounting = compute_accounting_contract(
        [
            {
                "run_id": "fixture",
                "images_generated": 2,
                "images_feature_extracted": 4,
                "gpu_seconds": 1.0,
                "cpu_seconds": 2.0,
                "samples_at_first_decision": 1,
                "fixed_budget_samples": 2,
                "retrospective_savings": 1,
                "online_realized_savings": 0,
            }
        ]
    )
    assert "never interchangeable" in accounting["savings_separation"]
    gallery = qualitative_gallery_contract(
        [
            {
                "image_paths": ["a.png", "b.png"],
                "model_ids": ["a", "b"],
                "feature_space_decisions": {"inception": "A_BETTER"},
                "point_estimate_direction": "A",
                "certificate_status": "pilot_only",
                "first_decision_sample_count": 10,
                "limitations": ["illustrative"],
            }
        ]
    )
    assert "not proof" in gallery["distribution_claim_disclaimer"]


def test_runtime_taxonomy_and_adapter_matrix(tmp_path: Path) -> None:
    config = {
        "run_id": "fixture-runtime",
        "scale": "1k",
        "model_count": 1,
        "images_per_model": 8,
        "reference_images": 8,
        "gpu_count": 2,
        "shard_count": 2,
        "session_limit_minutes": 60,
        "fixed_setup_minutes": 1,
        "model_download_cache_minutes_per_model": 1,
        "generation_images_per_second_per_gpu": {"min": 1.0, "max": 2.0},
        "generation_batch_size": 2,
        "average_encoded_image_bytes": 100,
        "extractors": [{"feature_space_id": "inception", "images_per_second_per_gpu": {"min": 1.0, "max": 2.0}, "feature_dimension": 7, "bytes_per_value": 4, "batch_size": 2}],
        "merge_minutes": 1,
        "local_validation_minutes": 1,
        "planning_ram_gib": 8,
        "planning_vram_per_gpu_gib": 16,
        "claim_allowed": False,
    }
    config["configuration_hash"] = configuration_hash(config)
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    planned = build_runtime_plan(config_path, tmp_path / "planned.json")
    assert planned["value_class"] == PLANNING_ESTIMATE
    report = {
        "images_per_second": 4.0,
        "safe_batch_size": 4,
        "peak_vram_gib": 2.0,
        "download_time_seconds": 3.0,
        "model_load_time_seconds": 1.0,
        "smoke_generation_time_seconds": 0.5,
        "extractors": [{"feature_space_id": "inception", "images_per_second": 8.0, "safe_batch_size": 4}],
        "claim_allowed": False,
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    measured = build_runtime_plan(config_path, tmp_path / "measured.json", preflight_report=report_path)
    assert measured["value_class"] == DERIVED_FROM_MEASURED_PREFLIGHT
    assert measured["measured_preflight"]["seconds_per_image"]["value_class"] == MEASURED_PREFLIGHT

    matrix = write_adapter_conformance_matrix(tmp_path / "matrix.csv")
    assert matrix["rows"] >= 6
    with (tmp_path / "matrix.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(row["model_or_extractor"] == "inception" and "PASS" in row["status"] for row in rows)
    assert any(row["model_or_extractor"] == "dinov2" and row["status"] == "REGISTERED_NOT_SELECTED" for row in rows)


def test_builder_faithful_synthetic_closure_uses_real_builders(tmp_path: Path) -> None:
    result = run_builder_faithful_synthetic(tmp_path / "closure")
    assert result["status"] == "BUILDER_FAITHFUL_SYNTHETIC_CLOSURE_PASS"
    assert result["cache_groups"] == 3
    assert result["not_model_evidence"] is True
    assert result["claim_allowed"] is False


def test_readiness_reports_every_required_component() -> None:
    report = readiness_report()
    required = {
        "reference", "selected_profile", "study_freeze", "model_preflight_package",
        "extractor_preflight_package", "model_adapter_readiness", "extractor_adapter_readiness",
        "generation_package", "feature_package", "image_path_resolvability",
        "output_schema_compatibility", "feature_merge", "cache_v2", "family_freeze",
        "exact_next_action",
    }
    assert required == set(report["components"])
    assert report["top_level_status"] in {
        "RUN_READY_WAITING_FOR_REFERENCE",
        "RUN_READY_WAITING_FOR_REFERENCE_VALIDATION",
        "READY_TO_PREPARE_PREFLIGHT",
        "WAITING_FOR_KAGGLE_DIAGNOSTIC",
        "WAITING_FOR_KAGGLE_PREFLIGHT",
    }
    assert report["claim_allowed"] is False
