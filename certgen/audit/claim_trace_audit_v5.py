"""Audit V5 claim trace and result-injection contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
from certgen.paper.result_injection import validate_claim_trace


def audit_claim_trace_v5(contract_path: str | Path = "data/contracts/result_injection_contract_v5.json", trace_path: str | Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not Path(contract_path).exists():
        errors.append(f"missing result injection contract: {contract_path}")
        contract = {}
    else:
        contract = read_json(contract_path)
        for field in ["claim_trace_required_fields", "injection_rules", "placeholder_behavior"]:
            if field not in contract:
                errors.append(f"missing contract field: {field}")
    if trace_path:
        if not Path(trace_path).exists():
            errors.append(f"missing claim trace: {trace_path}")
        else:
            trace = read_json(trace_path)
            errors.extend(validate_claim_trace(trace))
            if trace.get("claim_allowed") is True and trace.get("evidence_status") != "claim_eligible":
                errors.append("claim trace allows claim before claim_eligible")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "claim_allowed": False, "evidence_status": "template_only", "contract_loaded": bool(contract)}


def write_claim_trace_audit_v5(json_out: str | Path = "data/results/v5_claim_trace_audit.json") -> dict[str, Any]:
    payload = audit_claim_trace_v5()
    write_json(payload, json_out)
    return payload
