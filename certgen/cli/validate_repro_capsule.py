"""Validate V4 reproducibility capsule."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.release.capsule import validate_capsule, write_capsule_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate V4 reproducibility capsule.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    result = validate_capsule(".")
    write_capsule_manifest("release/CAPSULE_MANIFEST.json")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(f"# V4 Reproducibility Capsule Validation\n\nPassed: `{result['passed']}`\n", encoding="utf-8")
    write_json(result, args.json_out)
    print(f"Capsule validation: {'passed' if result['passed'] else 'failed'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
