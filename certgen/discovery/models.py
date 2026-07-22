"""Typed contracts for bounded, content-addressed runtime discovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PackageType(str, Enum):
    DIAGNOSTIC_INPUT = "DIAGNOSTIC_INPUT"
    DIAGNOSTIC_OUTPUT = "DIAGNOSTIC_OUTPUT"
    PREFLIGHT_INPUT = "PREFLIGHT_INPUT"
    PREFLIGHT_OUTPUT = "PREFLIGHT_OUTPUT"
    GENERATION_INPUT = "GENERATION_INPUT"
    GENERATION_OUTPUT = "GENERATION_OUTPUT"
    FEATURE_INPUT = "FEATURE_INPUT"
    FEATURE_OUTPUT = "FEATURE_OUTPUT"
    MULTIPART_OUTPUT = "MULTIPART_OUTPUT"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


class CandidateForm(str, Enum):
    ZIP = "ZIP"
    EXTRACTED_DIRECTORY = "EXTRACTED_DIRECTORY"


class SelectionStatus(str, Enum):
    SELECTED_UNIQUE_VALID_PACKAGE = "SELECTED_UNIQUE_VALID_PACKAGE"
    DUPLICATE_IDENTICAL_COPY_DEDUPED = "DUPLICATE_IDENTICAL_COPY_DEDUPED"
    NO_MATCHING_PACKAGE = "NO_MATCHING_PACKAGE"
    AMBIGUOUS_MATCHING_PACKAGES = "AMBIGUOUS_MATCHING_PACKAGES"
    AMBIGUOUS_DIFFERENT_CONTENT = "AMBIGUOUS_DIFFERENT_CONTENT"


@dataclass(frozen=True)
class DiscoveryLimits:
    maximum_depth: int = 12
    maximum_candidates: int = 10_000
    maximum_package_members: int = 200_000
    maximum_uncompressed_bytes: int = 20 * 1024**3
    maximum_metadata_bytes: int = 4 * 1024**2
    maximum_compression_ratio: float = 1_000.0

    def validate(self) -> None:
        if self.maximum_depth < 0:
            raise ValueError("maximum_depth must be nonnegative")
        if self.maximum_candidates <= 0:
            raise ValueError("maximum_candidates must be positive")
        if self.maximum_package_members <= 0 or self.maximum_uncompressed_bytes <= 0:
            raise ValueError("archive limits must be positive")
        if self.maximum_metadata_bytes <= 0 or self.maximum_compression_ratio <= 0:
            raise ValueError("metadata and compression limits must be positive")


@dataclass(frozen=True)
class PackageIdentity:
    schema_version: str
    package_type: PackageType
    stage: str | None
    run_id: str | None
    study_hash: str | None
    configuration_hash: str | None
    profile_id: str | None
    scale: str | None
    created_at_utc: str | None
    claim_allowed: bool
    integrity_manifest: str | None
    completion_status: str | None
    scientific_identity_hash: str
    contract_version: str | None = None
    direction: str | None = None
    source_code_hash: str | None = None
    output_schema_version: str | None = None
    input_package_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["package_type"] = self.package_type.value
        return payload


@dataclass(frozen=True)
class PackageCandidate:
    path: Path
    form: CandidateForm
    package_sha256: str | None
    identity: PackageIdentity
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "form": self.form.value,
            "package_sha256": self.package_sha256,
            "identity": self.identity.to_dict(),
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class PackageRequirement:
    expected_package_type: PackageType | None = None
    expected_stage: str | None = None
    expected_study_hash: str | None = None
    expected_profile_id: str | None = None
    expected_configuration_hash: str | None = None
    expected_run_id: str | None = None
    expected_scale: str | None = None
    expected_package_sha256: str | None = None
    expected_scientific_identity_hash: str | None = None
    expected_source_code_hash: str | None = None
    expected_integrity_manifest: str | None = None
    expected_output_schema_version: str | None = None
    expected_input_package_sha256: str | None = None
    required_completion_status: str | tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.expected_package_type is not None:
            payload["expected_package_type"] = self.expected_package_type.value
        if isinstance(self.required_completion_status, tuple):
            payload["required_completion_status"] = list(self.required_completion_status)
        return payload


@dataclass(frozen=True)
class ExpectedPackageIdentity:
    """Versioned, portable identity bound into canonical notebooks and handoffs."""

    expected_package_sha256: str
    expected_scientific_identity_hash: str
    expected_configuration_hash: str
    expected_run_id: str
    expected_source_code_hash: str
    expected_integrity_manifest: str
    expected_output_schema_version: str
    expected_package_type: str
    expected_stage: str
    expected_study_hash: str | None = None
    expected_profile_id: str | None = None
    expected_scale: str | None = None
    schema_version: str = "certgen.expected_package_identity.v1"
    claim_allowed: bool = False

    def validate(self) -> None:
        if self.schema_version != "certgen.expected_package_identity.v1":
            raise ValueError("unsupported expected-package identity schema")
        if self.claim_allowed is not False:
            raise ValueError("expected-package identity must set claim_allowed=false")
        for field_name in (
            "expected_package_sha256",
            "expected_scientific_identity_hash",
            "expected_configuration_hash",
            "expected_source_code_hash",
        ):
            value = str(getattr(self, field_name))
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError(f"{field_name} must be a lowercase SHA-256")
        for field_name in (
            "expected_run_id",
            "expected_integrity_manifest",
            "expected_output_schema_version",
            "expected_package_type",
            "expected_stage",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExpectedPackageIdentity":
        allowed = {field_name for field_name in cls.__dataclass_fields__}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError("unknown expected-package identity fields: " + ", ".join(unknown))
        identity = cls(**payload)
        identity.validate()
        return identity


@dataclass(frozen=True)
class ScanReport:
    roots: tuple[str, ...]
    duration_seconds: float
    files_visited: int
    directories_visited: int
    candidates_found: int
    skipped_symlinks: int
    depth_limit_hits: int
    inaccessible_paths: int
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryResult:
    status: SelectionStatus
    requirement: PackageRequirement
    candidates: tuple[PackageCandidate, ...]
    matching_candidates: tuple[PackageCandidate, ...]
    selected: PackageCandidate | None
    scan: ScanReport
    reasons: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "certgen.discovery.result.v1",
            "status": self.status.value,
            "requirement": self.requirement.to_dict(),
            "search": self.scan.to_dict(),
            "candidates": [row.to_dict() for row in self.candidates],
            "matching_candidates": [row.to_dict() for row in self.matching_candidates],
            "selected": self.selected.to_dict() if self.selected else None,
            "reasons": {key: list(value) for key, value in self.reasons.items()},
            "remediation": (
                "Attach or copy one package whose internal identity matches the requirement."
                if self.status is SelectionStatus.NO_MATCHING_PACKAGE
                else "Remove different-content exact matches or bind the expected package SHA-256."
                if self.status in {SelectionStatus.AMBIGUOUS_MATCHING_PACKAGES, SelectionStatus.AMBIGUOUS_DIFFERENT_CONTENT}
                else "No remediation required."
            ),
            "claim_allowed": False,
        }
