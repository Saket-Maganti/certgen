import json

from certgen.audit.forensic_final_audit import _claim_true_json_paths, _has_claim_true


def test_nested_claim_true_detection(tmp_path):
    assert _has_claim_true({"nested": [{"claim_allowed": True}]}) is True
    assert _has_claim_true({"claim_allowed": False}) is False

    data = tmp_path / "data"
    data.mkdir()
    (data / "safe.json").write_text(json.dumps({"claim_allowed": False}), encoding="utf-8")
    (data / "unsafe.json").write_text(
        json.dumps({"nested": {"claim_allowed": True}}), encoding="utf-8"
    )
    assert _claim_true_json_paths(tmp_path) == ["data/unsafe.json"]
