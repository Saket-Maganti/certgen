"""Compatibility CLI for the R0 technical-correction audit."""

from __future__ import annotations

from certgen.cli.r0_technical_audit import main, run_r0_technical_audit


__all__ = ["main", "run_r0_technical_audit"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
