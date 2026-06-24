import pytest

from certgen.certs.clean_core import make_clean_metric_certificate
from certgen.metrics.streams import clip_stream_values
from certgen.stats.design_contracts import CSConfig, ComparisonStream


def _bounded_stream(values):
    clipped = clip_stream_values(values, -1, 1)
    stream = ComparisonStream("cmp", "mmd_rbf", clipped.values, evidence_status="smoke_only", bounded=True, lower_bound=-1, upper_bound=1)
    stream.metadata["boundedness_metadata"] = clipped.metadata
    return stream


def test_negative_positive_and_near_zero_decisions():
    neg = make_clean_metric_certificate(_bounded_stream([-0.95] * 64), CSConfig(0.05, 64, -1, 1, method="hoeffding"))
    pos = make_clean_metric_certificate(_bounded_stream([0.95] * 64), CSConfig(0.05, 64, -1, 1, method="hoeffding"))
    zero = make_clean_metric_certificate(_bounded_stream([0.0] * 64), CSConfig(0.05, 64, -1, 1, method="hoeffding"))
    assert neg.decision == "A_certified_better"
    assert pos.decision == "B_certified_better"
    assert zero.decision == "not_decided_at_budget"
    assert neg.evidence_status == "smoke_only"
    assert neg.time_uniform is True


def test_unbounded_stream_rejected():
    stream = ComparisonStream("cmp", "mmd_rbf", [0.1], evidence_status="smoke_only")
    with pytest.raises(ValueError, match="bounded"):
        make_clean_metric_certificate(stream, CSConfig(0.05, 1, -1, 1))
