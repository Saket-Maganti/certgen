"""V9 paper firewall for blocked empirical claims."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


CLAIM_KEY = "claim_allowed"
CLAIM_EQUALS_TRUE = f"{CLAIM_KEY}=true"
CLAIM_JSON_TRUE = f'"{CLAIM_KEY}": true'
FORBIDDEN_PHRASES = [
    "pilot-only proves",
    "paper evidence",
    CLAIM_EQUALS_TRUE,
    CLAIM_JSON_TRUE,
    "final undecided fraction is",
    "we find that reported wins",
    "answer with real benchmarks",
    "our results demonstrate",
    "our results show",
]
SAFE_PLACEHOLDERS = ["TBD_REAL_RUN_REQUIRED", "NO_REAL_EVIDENCE", "not paper evidence", "placeholder"]


def _has_claim_allowed_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (key == "claim_allowed" and item is True) or _has_claim_allowed_true(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def _line_is_explicitly_guarded(line: str) -> bool:
    lowered = line.lower()
    guards = [
        "no_real_evidence",
        "not paper evidence",
        "no paper evidence",
        "not yet measured",
        "will report",
        "would report",
        "planned",
        "future work",
        "placeholder",
        "tbd_real_run_required",
        "forbidden",
        "must not",
        "cannot",
        "is blocked",
        "requires real",
    ]
    return any(guard in lowered for guard in guards)


def run_firewall(out_json: str | Path = "data/results/v9_paper_firewall.json", out_report: str | Path = "docs/V9_PAPER_FIREWALL_REPORT.md") -> dict[str, Any]:
    checked: list[str] = []
    blockers: list[str] = []
    from certgen.max_ceiling.contracts import validate_claims

    claim_matrix_path = Path("reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv")
    claim_matrix: dict[str, Any] = (
        validate_claims(matrix_path=claim_matrix_path)
        if claim_matrix_path.is_file()
        else {
            "status": "NOT_APPLICABLE_OUTSIDE_REPOSITORY_FIXTURE",
            "passed": True,
            "rows": 0,
            "claim_allowed": False,
        }
    )
    matrix_errors = claim_matrix.get("errors", [])
    if not isinstance(matrix_errors, list):
        matrix_errors = ["claim matrix errors field is not a list"]
    if not claim_matrix["passed"]:
        blockers.extend(f"claim-evidence matrix: {str(error)}" for error in matrix_errors)
    for root in [Path("paper"), Path("docs/paper")]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".tex", ".md", ".json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            checked.append(str(path))
            lowered = text.lower()
            if path.suffix == ".json":
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError as exc:
                    blockers.append(f"{path}: invalid JSON: {exc}")
                else:
                    if _has_claim_allowed_true(parsed):
                        blockers.append(f"{path}: structured claim_allowed=true")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for phrase in FORBIDDEN_PHRASES:
                    if phrase.lower() not in line.lower():
                        continue
                    # A placeholder elsewhere in a file cannot launder this line.
                    if _line_is_explicitly_guarded(line):
                        continue
                    blockers.append(
                        f"{path}:{line_number}: forbidden unguarded phrase `{phrase}`"
                    )
            if path.name.lower().startswith("table") and "TBD_REAL_RUN_REQUIRED" not in text and any(char.isdigit() for char in text):
                # Report as warning-like blocker only for tables that look numeric and unguarded.
                if "placeholder" not in lowered and "no_real_evidence" not in lowered:
                    blockers.append(f"{path}: numeric-looking table lacks placeholder/evidence guard")
    payload = {
        "passed": not blockers,
        "checked_files": checked,
        "blockers": blockers,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
        "claim_evidence_matrix": claim_matrix,
    }
    write_json(payload, out_json)
    lines = [
        "# V9 Paper Firewall Report",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Passed: `{payload['passed']}`",
        "Claim allowed: `false`",
        "",
        "## Blockers",
    ]
    lines.extend(f"- {item}" for item in blockers or ["none"])
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", default="data/results/v9_paper_firewall.json")
    parser.add_argument("--out-report", default="docs/V9_PAPER_FIREWALL_REPORT.md")
    args = parser.parse_args(argv)
    payload = run_firewall(args.out_json, args.out_report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
