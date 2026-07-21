from __future__ import annotations

import json
from pathlib import Path

import pytest

from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
from certgen.cvpr.family_certificates import run_family_certificates
from certgen.cvpr.ranking import build_partial_ranking


def test_builder_faithful_rehearsal_covers_post_cache_gates_and_full_family(tmp_path: Path) -> None:
    root = tmp_path / "closure"
    result = run_builder_faithful_synthetic(root)
    assert result["metric_reproduction_status"] == "PASS"
    assert result["sanity_controls_status"] == "PASS"
    assert result["family_certificate_coverage_status"] == "FAMILY_CERTIFICATES_COMPLETE"
    coverage = json.loads((root / "certificates" / "family_certificate_coverage.json").read_text(encoding="utf-8"))
    assert coverage["expected_hypotheses"] == 2
    assert coverage["completed_hypotheses"] == 2
    assert coverage["missing_hypotheses"] == []
    ranking = json.loads((root / "ranking" / "ranking_graph.json").read_text(encoding="utf-8"))
    assert ranking["missing_hypotheses"] == []


def test_family_runner_is_idempotent_and_reuses_valid_certificates(tmp_path: Path) -> None:
    root = tmp_path / "closure"
    run_builder_faithful_synthetic(root)
    family = json.loads((root / "family" / "family.json").read_text(encoding="utf-8"))
    study = __import__("yaml").safe_load((root / "study.yaml").read_text(encoding="utf-8"))
    operational = (
        root
        / "certificate_inputs"
        / study["configuration_hash"]
        / family["family_id"]
        / "family_operational_status.json"
    )
    result = run_family_certificates(
        study_path=root / "study.yaml",
        family_path=root / "family" / "family.json",
        inputs_root=root / "certificate_inputs",
        reference_draw_plan=root / "reference_draw_plan.json",
        metric_result=root / "metric_reproduction.json",
        sanity_result=root / "sanity_controls.json",
        operational_status=operational,
        out_dir=root / "certificates",
        registry_path=root / "artifact_registry.jsonl",
    )
    assert result["status"] == "FAMILY_CERTIFICATES_COMPLETE"
    assert sorted(result["reused_hypotheses"]) == sorted(
        row["hypothesis_id"] for row in family["hypotheses"]
    )


def test_ranking_refuses_incomplete_frozen_family(tmp_path: Path) -> None:
    root = tmp_path / "closure"
    run_builder_faithful_synthetic(root)
    certificates = sorted(
        path
        for path in (root / "certificates").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("schema_version")
        == "certgen.cvpr.certificate.v1"
    )
    assert len(certificates) == 2
    with pytest.raises(ValueError, match="complete frozen-family certificate coverage"):
        build_partial_ranking(
            certificates[:-1],
            out_dir=root / "incomplete_ranking",
            family_path=root / "family" / "family.json",
        )
