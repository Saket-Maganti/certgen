"""Release license field scan."""

from __future__ import annotations

from pathlib import Path


def scan_license_fields(root: str | Path = ".") -> list[str]:
    root = Path(root)
    issues = []
    for path in (root / "registry").glob("**/*.csv"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "license" in text.lower() and "unknown" in text.lower():
            issues.append(f"unknown license present in template: {path}")
    return issues
