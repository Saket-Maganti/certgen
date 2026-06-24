"""V5 release, anonymity, and privacy scan."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


SCAN_DIRS = ["docs", "paper", "release", "commands", "notebooks/generated", "data/contracts", "registry/related_work"]
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"api[_-]?key\s*[:=]", re.I),
    re.compile(r"token\s*[:=]\s*[A-Za-z0-9_\-]{16,}", re.I),
]
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LOCAL_PATH_PATTERN = re.compile(r"/Users/[A-Za-z0-9._-]+")


def scan_release_safety_v5(root: str | Path = ".", max_bytes: int = 10_000_000) -> dict[str, Any]:
    root = Path(root)
    issues: list[str] = []
    warnings: list[str] = []
    for rel in SCAN_DIRS:
        base = root / rel
        if not base.exists():
            continue
        for path in base.glob("**/*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            size = path.stat().st_size
            if size > max_bytes:
                issues.append(f"oversized release file: {path}")
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if LOCAL_PATH_PATTERN.search(text):
                issues.append(f"private local path: {path}")
            if EMAIL_PATTERN.search(text):
                issues.append(f"email address: {path}")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                issues.append(f"secret-like token: {path}")
            if re.search(r"\b\d{1,3}(?:\.\d+)?\s*%\b", text) and "TBD_REAL_RUN_REQUIRED" not in text and "threshold" not in text.lower():
                issues.append(f"percent-like result number without placeholder: {path}")
    for base in [root / "data/smoke", root / "data/results"]:
        if not base.exists():
            continue
        for path in base.glob("**/*.json"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if '"claim_allowed": true' in text:
                issues.append(f"claim leak in non-evidence tree: {path}")
    return {"passed": not issues, "issues": issues, "warnings": warnings, "claim_allowed": False, "evidence_status": "template_only", "release_profile": "anonymous_cvpr"}


def write_release_safety_v5(out: str | Path = "docs/release/ANONYMITY_AND_PRIVACY_AUDIT_V5.md", json_out: str | Path = "data/results/v5_release_safety.json") -> dict[str, Any]:
    payload = scan_release_safety_v5(".")
    lines = ["# Anonymity and Privacy Audit V5", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{payload['passed']}`", f"Release profile: `{payload['release_profile']}`", "", "## Issues"]
    lines.extend(f"- {issue}" for issue in payload["issues"] or ["none"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V5 release safety scan.")
    parser.add_argument("--out", default="docs/release/ANONYMITY_AND_PRIVACY_AUDIT_V5.md")
    parser.add_argument("--json-out", default="data/results/v5_release_safety.json")
    args = parser.parse_args(argv)
    payload = write_release_safety_v5(args.out, args.json_out)
    print(f"V5 release safety: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
