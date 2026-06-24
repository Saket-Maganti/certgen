"""Validate V3 registry tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.registry.v3_schema import validate_v3_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CertGen V3 registry tables.")
    parser.add_argument("--benchmarks", required=True)
    parser.add_argument("--model-pairs", required=True)
    parser.add_argument("--feature-caches", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    result = validate_v3_registry(args.benchmarks, args.model_pairs, args.feature_caches)
    lines = ["# V3 Registry Validation", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{result['passed']}`", "", "## Errors"]
    lines.extend(f"- {e}" for e in result["errors"] or ["none"])
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {w}" for w in result["warnings"] or ["none"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(result, args.json_out)
    print(f"V3 registry validation: {'passed' if result['passed'] else 'failed'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
