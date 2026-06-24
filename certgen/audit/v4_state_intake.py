"""V4 state intake and destructive audit checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json


SAFE_GUARDS = ["planned", "template", "no real result", "NO_REAL_EVIDENCE", "not paper evidence", "non-claim"]


def _check_artifact(path: Path) -> tuple[bool, str]:
    try:
        data = read_json(path)
    except Exception:
        return True, "not JSON object"
    text = json.dumps(data).lower()
    if path.match("data/smoke/**") and data.get("claim_allowed") is True:
        return False, "smoke/synthetic artifact has claim_allowed=true"
    if ("fid" in text or "fd_dinov2" in text) and ("rigorous_anytime_certificate" in text and "true" in text):
        return False, "FID/FD artifact claims rigorous certificate"
    return True, "ok"


def run_v4_state_intake(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    def add(name: str, passed: bool, detail: str, *, warning: bool = False) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail, "warning": warning})
        if not passed:
            (warnings if warning else blockers).append(f"{name}: {detail}")

    for directory in ["certgen", "certgen/certs", "certgen/audit", "certgen/registry", "docs", "tests"]:
        add(f"dir_{directory}", (root / directory).is_dir(), directory)
    for doc in ["docs/V1_SINGLE_FILE_HANDOFF.md", "docs/V2_SINGLE_FILE_HANDOFF.md", "docs/V3_SINGLE_FILE_HANDOFF.md"]:
        add(f"handoff_{Path(doc).stem}", (root / doc).exists(), doc, warning=not (root / doc).exists())
    for artifact in (root / "data").glob("**/*.json"):
        ok, detail = _check_artifact(artifact)
        add(f"artifact_{artifact}", ok, detail)
    no_results = root / "docs/NO_RESULTS_YET.md"
    add("result_boundary_doc_exists", no_results.exists(), str(no_results))
    fid_docs = [p for p in (root / "docs").glob("*FID*POLICY*.md")]
    add("fid_policy_docs_descriptive", bool(fid_docs) and all("descriptive" in p.read_text(encoding="utf-8").lower() for p in fid_docs), "FID docs descriptive")
    for path in [root / "registry", root / "registry/v3", root / "registry/provenance"]:
        if path.exists():
            for template in path.glob("*template*"):
                if not template.is_file():
                    continue
                text = template.read_text(encoding="utf-8", errors="ignore").lower()
                add(f"template_non_evidence_{template}", "no_real_evidence" in text or "template" in text or "planned" in text, str(template))
    risky_docs = []
    for path in (root / "docs").glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        for phrase in ["undecided fraction", "ranking changed", "real audit result", "published wins"]:
            if phrase in lowered and not any(guard.lower() in lowered for guard in SAFE_GUARDS):
                risky_docs.append(f"{path}:{phrase}")
    add("paper_claim_phrases_guarded", not risky_docs, "; ".join(risky_docs) if risky_docs else "guarded")
    abs_paths = []
    for path in (root / "docs").glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "/Users/" in text and "run note" not in text.lower():
            abs_paths.append(str(path))
    add("no_release_doc_private_paths", not abs_paths, "; ".join(abs_paths) if abs_paths else "none")
    add("tests_discoverable", any((root / "tests").glob("test_*.py")), "pytest tests present")
    return {
        "audit_name": "v4_state_intake",
        "passed": not blockers,
        "num_checks": len(checks),
        "num_passed": sum(1 for c in checks if c["passed"]),
        "num_failed": sum(1 for c in checks if not c["passed"] and not c["warning"]),
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "evidence_status": "dry_run_only",
        "claim_allowed": False,
    }


def write_v4_state_intake(out: str | Path, json_out: str | Path, root: str | Path = ".") -> dict[str, Any]:
    payload = run_v4_state_intake(root)
    lines = ["# V4 State Intake Audit", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{payload['passed']}`", "", "| Check | Status | Detail |", "|---|---:|---|"]
    for check in payload["checks"]:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {check['detail']} |")
    lines.extend(["", "## Blockers"])
    lines.extend(f"- {b}" for b in payload["blockers"] or ["none"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run V4 state intake audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = write_v4_state_intake(args.out, args.json_out)
    print(f"V4 state intake: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
