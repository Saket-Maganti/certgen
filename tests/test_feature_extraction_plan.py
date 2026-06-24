import json

import pytest

from certgen.cli.plan_feature_extraction import write_feature_extraction_plan
from certgen.features.extractors import EXTRACTORS
from certgen.features.extractors.base import OptionalDependencyMissing


def test_dry_run_feature_extraction_plan(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    existing = tmp_path / "image.png"
    existing.write_text("fake", encoding="utf-8")
    manifest.write_text(json.dumps({"sample_id": "1", "path": str(existing), "source_type": "reference_real"}) + "\n" + json.dumps({"sample_id": "2", "path": str(tmp_path / "missing.png"), "source_type": "generated_sample"}) + "\n", encoding="utf-8")
    plan = write_feature_extraction_plan(input_manifest=str(manifest), extractor="inception_v3_pool3", out_dir=str(tmp_path / "out"), device="auto", batch_size=1, out=str(tmp_path / "plan.md"), json_out=str(tmp_path / "plan.json"))
    assert plan["item_count"] == 2
    assert plan["missing_local_files_count"] == 1
    assert plan["claim_allowed"] is False


def test_invalid_extractor_and_extract_error(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        write_feature_extraction_plan(input_manifest=str(tmp_path / "missing"), extractor="bad", out_dir=str(tmp_path), device="auto", batch_size=1, out=str(tmp_path / "x.md"), json_out=str(tmp_path / "x.json"))
    extractor = EXTRACTORS["inception_v3_pool3"]()
    monkeypatch.setattr(extractor, "is_available", lambda: False)
    with pytest.raises(OptionalDependencyMissing):
        extractor.extract(str(tmp_path / "missing"), str(tmp_path), 1, "cpu")
