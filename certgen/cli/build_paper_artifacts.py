"""Build V4 paper artifact specs."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.reporting.figures import figure_specs
from certgen.reporting.result_cards import comparison_result_card
from certgen.reporting.tables import table_specs


def build_paper_artifacts(out_dir: str | Path, report: str | Path) -> dict:
    out_dir = Path(out_dir)
    payload = {"figures": figure_specs(), "tables": table_specs(), "result_cards": [comparison_result_card("comparison_template")], "claim_allowed": False, "evidence_status": "planned_only"}
    write_json(payload, out_dir / "paper_artifacts_spec.json")
    lines = ["# Paper Artifacts V4", "", "`NON-EVIDENCE / TEMPLATE / SYNTHETIC`", "", f"- Figures: `{len(payload['figures'])}`", f"- Tables: `{len(payload['tables'])}`", "- Paper-ready status: `false`"]
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V4 non-claim paper artifact specs.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    build_paper_artifacts(args.out_dir, args.report)
    print(f"Wrote paper artifact specs: {args.out_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
