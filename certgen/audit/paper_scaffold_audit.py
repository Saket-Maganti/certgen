"""V5 main-paper scaffold audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.reporting.result_contracts import PLACEHOLDER_TOKEN


REQUIRED_PAPER_FILES = [
    "paper/main.tex",
    "paper/sections/00_abstract.tex",
    "paper/sections/01_introduction.tex",
    "paper/sections/02_related_work.tex",
    "paper/sections/03_method.tex",
    "paper/sections/04_experimental_protocol.tex",
    "paper/sections/05_results_placeholder.tex",
    "paper/sections/06_limitations_ethics.tex",
    "paper/sections/07_conclusion.tex",
    "docs/paper/PAPER_BUILD_GUIDE.md",
]

FORBIDDEN_RESULT_PHRASES = [
    "we show that",
    "our results demonstrate",
    "published wins are undecided",
    "ranking changes",
    "model a is better",
    "most papers are wrong",
]


def audit_paper_scaffold(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    for rel in REQUIRED_PAPER_FILES:
        if not (root / rel).exists():
            errors.append(f"missing paper file: {rel}")
    for rel in REQUIRED_PAPER_FILES:
        path = root / rel
        if not path.exists() or path.suffix != ".tex":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in FORBIDDEN_RESULT_PHRASES:
            if phrase in text:
                errors.append(f"{rel}: forbidden result phrase '{phrase}'")
    results = root / "paper/sections/05_results_placeholder.tex"
    if results.exists() and PLACEHOLDER_TOKEN not in results.read_text(encoding="utf-8", errors="ignore"):
        errors.append("results section missing TBD_REAL_RUN_REQUIRED")
    limitations = root / "paper/sections/06_limitations_ethics.tex"
    if limitations.exists():
        lower = limitations.read_text(encoding="utf-8", errors="ignore").lower()
        if "fid" not in lower or "descriptive" not in lower:
            errors.append("limitations section must include FID descriptive-only policy")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "claim_allowed": False, "evidence_status": "template_only"}


def write_paper_scaffold_audit(json_out: str | Path = "data/results/v5_paper_scaffold_audit.json") -> dict[str, Any]:
    payload = audit_paper_scaffold()
    write_json(payload, json_out)
    return payload
