"""Single source of truth for worker identity and completion-marker compatibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


WORKER_CONTRACT_VERSION = "certgen.worker_contract.v1"
COMPLETION_SCHEMA_VERSION = "certgen.worker_completion.v3"
LEGACY_COMPLETION_SCHEMA_VERSION = "certgen.worker_completion.v2"

IMPLEMENTATION_VERSIONS = {
    "diagnostic": "certgen.diagnostic_worker.v1",
    "preflight": "certgen.preflight_worker.v3",
    "extractor_preflight": "certgen.extractor_preflight_worker.v3",
    "generation": "certgen.generation_worker.v3",
    "feature": "certgen.feature_worker.v3",
    "fixture": "certgen.fixture_worker.v3",
}

LEGACY_COMPATIBLE_VERSIONS = {
    "diagnostic": set(),
    "preflight": {"certgen.worker.v2"},
    "extractor_preflight": {"certgen.worker.v3"},
    "generation": {"certgen.worker.v2"},
    "feature": {"certgen.worker.v3"},
    "fixture": {"certgen.worker.v2"},
}


def infer_worker_type(module: str) -> str:
    name = module.rsplit(".", 1)[-1]
    if name == "diagnostic_worker":
        return "diagnostic"
    if name == "extractor_preflight_worker":
        return "extractor_preflight"
    if name == "preflight_worker":
        return "preflight"
    if name in {"generation_worker", "fake_generation_worker"}:
        return "generation" if name == "generation_worker" else "fixture"
    if name == "feature_worker":
        return "feature"
    if name == "fake_worker":
        return "fixture"
    raise ValueError(f"unregistered worker module: {module}")


@dataclass(frozen=True)
class WorkerIdentity:
    worker_contract_version: str
    worker_type: str
    worker_implementation_version: str
    config_schema_version: str
    output_schema_version: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def worker_identity(
    worker_type: str,
    *,
    config_schema_version: str,
    output_schema_version: str,
) -> WorkerIdentity:
    if worker_type not in IMPLEMENTATION_VERSIONS:
        raise ValueError(f"unsupported worker_type: {worker_type}")
    if not config_schema_version or not output_schema_version:
        raise ValueError("worker config/output schema versions must be non-empty")
    return WorkerIdentity(
        WORKER_CONTRACT_VERSION,
        worker_type,
        IMPLEMENTATION_VERSIONS[worker_type],
        config_schema_version,
        output_schema_version,
    )


def completion_identity_fields(
    worker_type: str,
    *,
    config_schema_version: str,
    output_schema_version: str,
) -> dict[str, str]:
    identity = worker_identity(
        worker_type,
        config_schema_version=config_schema_version,
        output_schema_version=output_schema_version,
    )
    return {
        "schema_version": COMPLETION_SCHEMA_VERSION,
        **identity.as_dict(),
    }


def validate_completion_identity(
    payload: Mapping[str, Any],
    *,
    worker_type: str,
    config_schema_version: str | None = None,
    output_schema_version: str | None = None,
    allow_legacy: bool = True,
) -> dict[str, Any]:
    """Validate an exact current marker or one explicitly compatible legacy marker."""

    errors: list[str] = []
    compatibility = "current"
    schema = payload.get("schema_version")
    if schema == LEGACY_COMPLETION_SCHEMA_VERSION:
        compatibility = "legacy_compatible"
        legacy = str(payload.get("worker_version", ""))
        if not allow_legacy or legacy not in LEGACY_COMPATIBLE_VERSIONS.get(worker_type, set()):
            errors.append("legacy worker version is not compatible with the requested worker type")
        if not legacy:
            errors.append("completion marker is missing worker version identity")
        if any(key in payload for key in WorkerIdentity.__dataclass_fields__):
            errors.append("completion marker mixes legacy and current worker identity fields")
    elif schema == COMPLETION_SCHEMA_VERSION:
        if "worker_version" in payload:
            errors.append("completion marker mixes current and legacy worker identity fields")
        expected = worker_identity(
            worker_type,
            config_schema_version=config_schema_version or str(payload.get("config_schema_version", "")),
            output_schema_version=output_schema_version or str(payload.get("output_schema_version", "")),
        )
        for key, value in expected.as_dict().items():
            if payload.get(key) != value:
                errors.append(f"completion marker {key} mismatch")
    else:
        errors.append("completion marker schema/version is missing or unsupported")
    return {
        "passed": not errors,
        "compatibility": compatibility if not errors else "incompatible",
        "errors": errors,
        "worker_type": worker_type,
        "claim_allowed": False,
    }
