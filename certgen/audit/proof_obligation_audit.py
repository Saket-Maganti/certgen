"""V5 supplement/proof obligation audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json


REQUIRED_SUPPLEMENT_FILES = [
    "paper/supplement.tex",
    "paper/supplement/01_certificate_details.tex",
    "paper/supplement/02_optional_stopping_validity.tex",
    "paper/supplement/03_mmd_kid_cmmd_streams.tex",
    "paper/supplement/04_multiple_comparisons_dependence.tex",
    "paper/supplement/05_fid_fd_policy.tex",
    "paper/supplement/06_reproducibility_details.tex",
    "paper/supplement/07_additional_tables_placeholders.tex",
]


def default_proof_obligations() -> dict[str, Any]:
    descriptions = [
        "Define comparison estimand Delta = d(A,R) - d(B,R).",
        "State assumptions for bounded stream terms.",
        "State how stream terms are clipped or bounded.",
        "State the confidence sequence validity condition.",
        "State optional-stopping theorem or cited theorem.",
        "State stopping rule.",
        "State multiple-comparison alpha policy.",
        "State dependence caveats.",
        "State why FID is not part of the rigorous clean-core certificate unless separately handled.",
        "State what is empirical validation vs theoretical guarantee.",
    ]
    return {
        "proof_obligation_version": "0.5.0",
        "obligations": [
            {
                "obligation_id": f"PO{i:02d}",
                "description": desc,
                "status": "drafted",
                "requires_external_citation": i in {4, 5},
                "paper_location": "paper/supplement.tex",
                "audit_status": "draft_not_verified",
            }
            for i, desc in enumerate(descriptions, start=1)
        ],
        "claim_allowed": False,
        "evidence_status": "template_only",
    }


def audit_proof_obligations(path: str | Path = "data/contracts/proof_obligations_v5.json", root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    for rel in REQUIRED_SUPPLEMENT_FILES:
        if not (root / rel).exists():
            errors.append(f"missing supplement file: {rel}")
    if not Path(path).exists():
        errors.append(f"missing proof obligations: {path}")
        payload = {}
    else:
        payload = read_json(path)
        for obligation in payload.get("obligations", []):
            if obligation.get("status") == "verified" and not obligation.get("paper_location"):
                errors.append(f"{obligation.get('obligation_id')}: verified without paper location")
            if obligation.get("requires_external_citation") and obligation.get("status") == "verified":
                warnings.append(f"{obligation.get('obligation_id')}: external citation must remain source-checked")
    fid = root / "paper/supplement/05_fid_fd_policy.tex"
    if fid.exists():
        lower = fid.read_text(encoding="utf-8", errors="ignore").lower()
        required = ["nonlinear", "biased", "does not directly certify fid", "descriptive"]
        for token in required:
            if token not in lower:
                errors.append(f"FID appendix missing caveat token: {token}")
    opt = root / "paper/supplement/02_optional_stopping_validity.tex"
    if opt.exists() and "methodological validation" not in opt.read_text(encoding="utf-8", errors="ignore").lower():
        errors.append("optional-stopping section must say methodological validation")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "obligations": len(payload.get("obligations", [])) if payload else 0, "claim_allowed": False, "evidence_status": "template_only"}


def write_proof_obligations(path: str | Path = "data/contracts/proof_obligations_v5.json") -> dict[str, Any]:
    payload = default_proof_obligations()
    write_json(payload, path)
    return payload
