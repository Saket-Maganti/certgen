from __future__ import annotations

import hashlib
from pathlib import Path

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_legacy_pilot_hashes_and_new_10k_freeze() -> None:
    legacy = ROOT / "artifacts/cvpr/study/cifar_integrity_minimal.yaml"
    assert _sha(legacy) == "346f0bea70d94803bd9da2793153496a6b0c1fe839174e8d2049773f5bfcc5ae"
    assert _sha(ROOT / "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip") == "d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d"
    assert _sha(ROOT / "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip") == "d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f"
    link = yaml.safe_load((ROOT / "registry/icml2027/legacy_pilot_link.yaml").read_text())
    assert link["not_main_icml_confirmatory_study"] is True
    study = yaml.safe_load((ROOT / "configs/icml2027/cifar_confirmatory_10k_v1.yaml").read_text())
    assert study["study_id"] == "icml2027_cifar_confirmatory_10k_v1"
    assert study["prefix_policy"] == "single_frozen_maximum_stream_no_outcome_adaptive_selection"
    assert study["immutable"] is True
    assert study["claim_allowed"] is False
