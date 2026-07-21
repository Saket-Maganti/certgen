from pathlib import Path

from certgen.cvpr.prepare import prepare_family
from certgen.cvpr.profiles import load_profile
from certgen.cvpr.study import freeze_study


def test_minimal_profile_freezes_exact_two_hypothesis_model_family(
    tmp_path: Path,
) -> None:
    profile = load_profile("cifar_integrity_minimal")
    assert profile["comparisons"] == ["checkpoint_variant"]
    assert profile["controls"] == ["null_reference_split", "obvious_gap_corruption"]
    assert profile["controls_in_confirmatory_family"] is False
    assert profile["controls_claim_allowed"] is False

    study_path = tmp_path / "study.yaml"
    freeze_study("cifar_integrity_minimal", out_path=study_path)
    family = prepare_family(out_dir=tmp_path / "family", study_path=study_path)

    assert family["number_of_hypotheses"] == 2
    assert family["model_pairs"] == ["checkpoint_variant"]
    assert {row["feature_space"] for row in family["hypotheses"]} == {
        "inception",
        "clip",
    }
    assert family["controls_in_confirmatory_family"] is False
    assert family["controls_claim_allowed"] is False
    assert not ({row["comparison_id"] for row in family["hypotheses"]} & set(profile["controls"]))
