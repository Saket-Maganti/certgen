"""Deterministic exact-identity selection with fail-closed ambiguity."""

from __future__ import annotations

from certgen.discovery.models import PackageCandidate, PackageRequirement


def mismatch_reasons(candidate: PackageCandidate, requirement: PackageRequirement) -> tuple[str, ...]:
    if not candidate.valid:
        return ("candidate is invalid", *candidate.errors)
    identity = candidate.identity
    checks = (
        ("package_sha256", candidate.package_sha256, requirement.expected_package_sha256),
        ("package_type", identity.package_type, requirement.expected_package_type),
        ("stage", identity.stage, requirement.expected_stage),
        ("study_hash", identity.study_hash, requirement.expected_study_hash),
        ("profile_id", identity.profile_id, requirement.expected_profile_id),
        ("configuration_hash", identity.configuration_hash, requirement.expected_configuration_hash),
        ("run_id", identity.run_id, requirement.expected_run_id),
        ("scale", identity.scale, requirement.expected_scale),
        ("scientific_identity_hash", identity.scientific_identity_hash, requirement.expected_scientific_identity_hash),
        ("source_code_hash", identity.source_code_hash, requirement.expected_source_code_hash),
        ("integrity_manifest", identity.integrity_manifest, requirement.expected_integrity_manifest),
        ("output_schema_version", identity.output_schema_version, requirement.expected_output_schema_version),
        ("input_package_sha256", identity.input_package_sha256, requirement.expected_input_package_sha256),
    )
    reasons = [f"{name} mismatch: observed={observed!r}, expected={expected!r}" for name, observed, expected in checks if expected is not None and observed != expected]
    required = requirement.required_completion_status
    if required is not None:
        accepted = (required,) if isinstance(required, str) else required
        if identity.completion_status not in accepted:
            reasons.append(
                f"completion_status mismatch: observed={identity.completion_status!r}, expected one of={accepted!r}"
            )
    return tuple(reasons)
