"""Explicit acceptance-path coverage for the released-sample importer."""

from certgen.icml2027.released_samples import assess_protocol_compatibility


def test_generated_and_released_protocols_require_explicit_verified_compatibility() -> None:
    generated = {
        "model_id": "m",
        "benchmark_id": "b",
        "resolution": "32x32",
        "conditioning": "none",
        "class_balance": "balanced",
        "sampling_protocol": "frozen-v1",
        "sampling_protocol_verified": True,
    }
    released = {**generated, "sampling_protocol_verified": False}
    blocked = assess_protocol_compatibility(generated, released)
    assert blocked["decision"] == "KEEP_IN_SEPARATE_FAMILIES"
    assert blocked["compatible_for_shared_confirmatory_family"] is False
    released["sampling_protocol_verified"] = True
    assert assess_protocol_compatibility(generated, released)["compatible_for_shared_confirmatory_family"] is True
