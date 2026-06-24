from certgen.certs.confidence_sequence import update_empirical_bernstein_cs
from certgen.certs.decision import make_decision_certificate
from certgen.core.enums import EvidenceStatus
from certgen.metrics.registry import metric_record_from_registry
from certgen.reporting.certificate_report import certificate_report_markdown
from certgen.gates.claim_gate import scan_text_for_forbidden_claims
from certgen.schemas.comparison import ComparisonRecord


def _comparison(metric_name="mmd_rbf"):
    return ComparisonRecord(
        comparison_id=f"{metric_name}_comparison",
        dataset_id="toy",
        model_a_id="a",
        model_b_id="b",
        reference_id="r",
        metric_name=metric_name,
        alpha=0.05,
        max_samples=64,
        evidence_status=EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )


def test_negative_delta_stream_certifies_a_status_in_smoke_mode():
    cert = make_decision_certificate(
        _comparison(),
        [-0.95] * 64,
        0.05,
        64,
        metric_record_from_registry("mmd_rbf"),
        EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )
    assert cert.status == "certified_a_better"
    assert cert.evidence_status == "non_evidence_smoke"


def test_positive_delta_stream_certifies_b_status_in_smoke_mode():
    cert = make_decision_certificate(
        _comparison(),
        [0.95] * 64,
        0.05,
        64,
        metric_record_from_registry("cmmd_clip_mmd"),
        EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )
    assert cert.status == "certified_b_better"
    assert cert.evidence_status == "non_evidence_smoke"


def test_near_zero_stream_not_decided_at_budget():
    cert = make_decision_certificate(
        _comparison(),
        [0.0] * 64,
        0.05,
        64,
        metric_record_from_registry("mmd_rbf"),
        EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )
    assert cert.status == "not_decided_at_budget"


def test_fid_rejected_from_clean_certificate_path_as_descriptive_only():
    cert = make_decision_certificate(
        _comparison("fid_inception"),
        [0.95] * 64,
        0.05,
        64,
        metric_record_from_registry("fid_inception"),
        EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )
    assert cert.status == "descriptive_only"
    assert cert.optional_stopping_valid is False


def test_optional_stopping_valid_false_for_observed_range_fallback():
    states = update_empirical_bernstein_cs([0.1, 0.2, 0.3], alpha=0.05, value_range=None)
    assert states[-1].optional_stopping_valid is False


def test_certificate_report_wording_passes_claim_gate():
    cert = make_decision_certificate(
        _comparison(),
        [0.0] * 64,
        0.05,
        64,
        metric_record_from_registry("mmd_rbf"),
        EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    )
    report = certificate_report_markdown(cert)
    assert scan_text_for_forbidden_claims(report, evidence_status="non_evidence_smoke").passed
