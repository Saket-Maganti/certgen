from certgen.certs.decision import make_decision_certificate
from certgen.core.enums import EvidenceStatus
from certgen.gates.fid_policy_gate import validate_fid_certificate_request
from certgen.metrics.registry import metric_record_from_registry
from certgen.schemas.comparison import ComparisonRecord


def _comparison(metric_name="fid_inception"):
    return ComparisonRecord(
        comparison_id="fid_policy_test",
        dataset_id="toy",
        model_a_id="a",
        model_b_id="b",
        reference_id="r",
        metric_name=metric_name,
        alpha=0.05,
        max_samples=10,
        evidence_status=EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )


def test_fid_cannot_enter_clean_cs_path():
    record = metric_record_from_registry("fid_inception")
    decision = validate_fid_certificate_request(record, "clean_cs", "smoke")
    assert not decision.passed


def test_fid_descriptive_artifact_has_limitations_and_no_optional_stopping_validity():
    record = metric_record_from_registry("fid_inception")
    cert = make_decision_certificate(
        _comparison(),
        [0.1, 0.2, 0.3],
        0.05,
        10,
        record,
        EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )
    assert cert.status == "descriptive_only"
    assert cert.optional_stopping_valid is False
    assert cert.limitations


def test_fd_dinov2_not_marked_clean_cs_supported():
    record = metric_record_from_registry("fd_dinov2")
    assert record.supports_clean_cs is False
    assert record.fid_rigor_status == "descriptive_only"
