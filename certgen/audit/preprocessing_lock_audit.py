"""Audit preprocessing lock files."""

from __future__ import annotations

from certgen.preprocess.locks import validate_preprocessing_lock


def audit_preprocessing_lock(path: str, *, strict: bool = True) -> dict:
    errors = validate_preprocessing_lock(path, strict=strict)
    return {"passed": not errors, "errors": errors, "evidence_status": "planned_only", "claim_allowed": False}
