"""Approved search-root construction without broad filesystem crawling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


KAGGLE_DEFAULT_ROOTS = (Path("/kaggle/input"), Path("/kaggle/working"))
LOCAL_RELATIVE_ROOTS = (
    Path("data/kaggle_returns"),
    Path("artifacts/cvpr/incoming"),
    Path("artifacts/cvpr/returned"),
    Path("incoming"),
    Path("."),
)


def configured_roots(
    roots: Iterable[str | Path] | None = None,
    *,
    repository_root: str | Path | None = None,
    kaggle: bool = False,
    include_environment: bool = True,
) -> tuple[Path, ...]:
    values: list[Path] = []
    if roots:
        values.extend(Path(value).expanduser() for value in roots)
    elif kaggle:
        values.extend(KAGGLE_DEFAULT_ROOTS)
    elif repository_root is not None:
        base = Path(repository_root)
        values.extend(base / relative for relative in LOCAL_RELATIVE_ROOTS)
    if include_environment:
        raw = os.environ.get("CERTGEN_SEARCH_ROOTS", "")
        values.extend(Path(value).expanduser() for value in raw.split(os.pathsep) if value)
    unique: list[Path] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.resolve(strict=False)
        key = os.path.normcase(str(normalized))
        if key not in seen:
            seen.add(key)
            unique.append(normalized)
    return tuple(unique)


def normalized_root_label(root: Path, *, repository_root: str | Path | None = None) -> str:
    resolved = root.resolve(strict=False)
    if repository_root is not None:
        try:
            relative = resolved.relative_to(Path(repository_root).resolve(strict=False))
            return "." if not relative.parts else relative.as_posix()
        except ValueError:
            pass
    if str(resolved).startswith("/kaggle/"):
        return str(resolved)
    return "<explicit-external-root>"
