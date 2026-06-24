"""Run release safety scan."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.release.license_scan import scan_license_fields
from certgen.release.privacy_scan import scan_privacy


def run_scan(out: str, json_out: str) -> dict:
    privacy = scan_privacy(".")
    license_issues = scan_license_fields(".")
    issues = privacy + license_issues
    payload = {"passed": not privacy, "issues": issues, "privacy_issues": privacy, "license_warnings": license_issues, "claim_allowed": False}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    lines = ["# V4 Release Safety Report", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{payload['passed']}`", "", "## Issues"]
    lines.extend(f"- {i}" for i in issues or ["none"])
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V4 release safety scan.")
    parser.add_argument("--out", default="docs/V4_RELEASE_SAFETY_REPORT.md")
    parser.add_argument("--json-out", default="data/results/v4_release_safety.json")
    args = parser.parse_args(argv)
    payload = run_scan(args.out, args.json_out)
    print(f"Release safety scan: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
