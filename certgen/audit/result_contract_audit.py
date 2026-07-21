"""Audit V5 result contracts and manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.reporting.result_contracts import PLACEHOLDER_TOKEN, load_result_contracts, validate_result_contracts


def audit_result_contracts(path: str | Path = "data/contracts/result_contracts_v5.json") -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not Path(path).exists():
        errors.append(f"missing result contracts: {path}")
        payload = {}
    else:
        payload = load_result_contracts(path)
        errors.extend(validate_result_contracts(payload))
    for manifest in ["docs/paper/TABLE_MANIFEST_V5.md", "docs/paper/FIGURE_MANIFEST_V5.md"]:
        file_path = Path(manifest)
        if not file_path.exists():
            errors.append(f"missing manifest: {manifest}")
        elif PLACEHOLDER_TOKEN not in file_path.read_text(encoding="utf-8", errors="ignore"):
            errors.append(f"{manifest}: missing placeholder token")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "claim_allowed": False, "evidence_status": "template_only", "contracts": len(payload.get("items", [])) if payload else 0}


def write_result_contract_audit(json_out: str | Path = "data/results/v5_result_contract_audit.json") -> dict[str, Any]:
    payload = audit_result_contracts()
    write_json(payload, json_out)
    return payload
