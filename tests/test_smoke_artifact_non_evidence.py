from pathlib import Path

from certgen.cli.make_smoke_artifacts import create_smoke_artifacts
from certgen.core.io import read_json
from certgen.gates.claim_gate import scan_text_for_forbidden_claims


def test_smoke_artifacts_are_non_evidence(tmp_path):
    out_dir = tmp_path / "smoke"
    result = create_smoke_artifacts(
        config_path="configs/certgen_v1_smoke.yaml",
        out_dir=out_dir,
        compute_metrics=True,
        make_certificate=True,
    )
    assert result["evidence_status"] == "non_evidence_smoke"
    smoke = read_json(out_dir / "smoke_artifact.json")
    assert smoke["evidence_status"] == "non_evidence_smoke"
    metrics = read_json(out_dir / "metrics" / "smoke_metrics.json")
    assert metrics["evidence_status"] == "non_evidence_smoke"
    assert all(item["evidence_status"] == "non_evidence_smoke" for item in metrics["metrics"])
    certificate = read_json(out_dir / "certificates" / "smoke_mmd_rbf_certificate.json")
    assert certificate["evidence_status"] == "non_evidence_smoke"
    report = Path(out_dir / "reports" / "smoke_certificate_report.md").read_text(encoding="utf-8")
    assert scan_text_for_forbidden_claims(report, evidence_status="non_evidence_smoke").passed
