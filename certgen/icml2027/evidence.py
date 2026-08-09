"""Fail-closed claim ladder and authenticated-evidence audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.icml2027.common import load_mapping, write_csv, write_json


LEVELS = {
    "C0": "engineering correctness",
    "C1": "synthetic validity",
    "C2": "real 1k pilot observation",
    "C3": "CIFAR confirmatory result",
    "C4": "multi-model real result",
    "C5": "multi-benchmark real result",
    "C6": "theorem-backed general methodological claim",
}


def audit_evidence(registry_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    registry = load_mapping(registry_path)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for claim in registry.get("claims", []):
        level = str(claim.get("level", ""))
        if level not in LEVELS:
            errors.append(f"unknown claim level for {claim.get('claim_id')}: {level}")
            continue
        evidence = claim.get("evidence", [])
        authenticated_real = any(
            isinstance(item, dict)
            and item.get("authenticated") is True
            and item.get("synthetic") is False
            and item.get("fixture") is False
            for item in evidence
        )
        theorem_verified = bool(claim.get("theorem_verified", False))
        eligible = level in {"C0", "C1"} or (level == "C2" and authenticated_real)
        if level in {"C3", "C4", "C5"}:
            eligible = authenticated_real and bool(claim.get("prospective_contract_hash"))
        if level == "C6":
            eligible = authenticated_real and theorem_verified
        requested = bool(claim.get("claim_allowed", False))
        if requested:
            errors.append(f"registry claim_allowed must remain false: {claim.get('claim_id')}")
        rows.append(
            {
                "claim_id": claim.get("claim_id"),
                "level": level,
                "level_description": LEVELS[level],
                "authenticated_real_evidence": authenticated_real,
                "theorem_verified": theorem_verified,
                "promotion_eligible": eligible,
                "current_claim_allowed": False,
                "blocker": "" if eligible else "required authenticated evidence or verified theory is absent",
            }
        )
    target = Path(out_path)
    write_csv(target, rows)
    payload = {
        "schema_version": "certgen.icml2027.evidence_audit.v1",
        "claims": len(rows),
        "eligible": sum(bool(row["promotion_eligible"]) for row in rows),
        "errors": errors,
        "passed": not errors,
        "claim_allowed": False,
    }
    write_json(target.with_suffix(".json"), payload)
    return payload
