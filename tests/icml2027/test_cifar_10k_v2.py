from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]

from certgen.icml2027.study_v2 import validate_cifar_10k_v2


ROOT = Path(__file__).resolve().parents[2]


def test_v1_is_registered_superseded_and_v2_contract_validates() -> None:
    registry = yaml.safe_load((ROOT / "registry/icml2027/study_registry.yaml").read_text())
    rows = {row["study_id"]: row for row in registry["studies"]}
    assert rows["icml2027_cifar_confirmatory_10k_v1"]["status"] == "SUPERSEDED_BEFORE_EXECUTION_DO_NOT_RUN"
    assert rows["icml2027_cifar_confirmatory_10k_v2"]["status"] == "FROZEN_WAITING_AUTHENTICATED_GPU"
    result = validate_cifar_10k_v2(root=ROOT)
    assert result["passed"], result["errors"]


def test_v1_frozen_bytes_still_declare_original_design_for_provenance() -> None:
    study = yaml.safe_load((ROOT / "configs/icml2027/cifar_confirmatory_10k_v1.yaml").read_text())
    assert study["reference_draw"]["without_replacement"] is True
    assert study["immutable"] is True
