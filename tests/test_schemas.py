from certgen.core.hashing import stable_hash_json
from certgen.core.io import read_json, write_json
from certgen.schemas.audit_record import AuditClaimRecord
from certgen.schemas.certificate import DecisionCertificate
from certgen.schemas.comparison import ComparisonRecord
from certgen.schemas.dataset import DatasetRecord
from certgen.schemas.feature_manifest import FeatureManifest
from certgen.schemas.metric import MetricRecord
from certgen.schemas.model import ModelRecord


def _schema_instances():
    return [
        DatasetRecord("dataset", "Dataset", "split", "source", "license", 10, "non_evidence_smoke", "hash"),
        ModelRecord("model", "Model", "family", "source", True, "license", "non_evidence_smoke"),
        FeatureManifest("manifest", "dataset", "toy", 10, 2, {"resize": "none"}, "features.npz", "hash", "non_evidence_smoke"),
        MetricRecord("kid_poly", "kid", "toy", "unbiased", True, None, "non_evidence_smoke"),
        ComparisonRecord("comparison", "dataset", "a", "b", "ref", "kid_poly", 0.05, 128, "non_evidence_smoke"),
        DecisionCertificate("cert", "comparison", "kid_poly", 0.05, "not_decided_at_budget", None, 128, -0.1, 0.1, 0.0, True, None, "non_evidence_smoke", ["toy"], {}),
        AuditClaimRecord("claim", "pair", "TBD", "kid_poly", "TBD", None, None, None, "non_evidence_planned", ["planned"]),
    ]


def test_every_schema_serializes_and_deserializes(tmp_path):
    for index, instance in enumerate(_schema_instances()):
        path = tmp_path / f"schema_{index}.json"
        write_json(instance, path)
        loaded = read_json(path)
        assert isinstance(loaded, dict)
        assert loaded


def test_stable_hash_json_is_deterministic():
    obj_a = {"b": 2, "a": [1, 2, 3]}
    obj_b = {"a": [1, 2, 3], "b": 2}
    assert stable_hash_json(obj_a) == stable_hash_json(obj_b)
