"""Release privacy/secrets scan."""

from __future__ import annotations

import re
from pathlib import Path


SECRET_PATTERNS = [re.compile(r"sk-[A-Za-z0-9]{20,}"), re.compile(r"api[_-]?key\s*[:=]", re.I)]


def scan_privacy(root: str | Path = ".", max_bytes: int = 5_000_000) -> list[str]:
    root = Path(root)
    issues: list[str] = []
    for path in list((root / "docs").glob("**/*")) + list((root / "release").glob("**/*")):
        if not path.is_file() or path.stat().st_size > max_bytes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "/Users/" in text:
            issues.append(f"private absolute path: {path}")
        if any(p.search(text) for p in SECRET_PATTERNS):
            issues.append(f"secret-like pattern: {path}")
    return issues
