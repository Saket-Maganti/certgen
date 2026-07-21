from __future__ import annotations

import argparse
import json
from pathlib import Path


FORBIDDEN = [
    "fid certificate",
    "rigorous fid",
    "cvpr-ready empirical",
    "claim_allowed=true",
]


def audit(root: str | Path = "paper") -> dict[str, object]:
    root = Path(root)
    hits = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".tex"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in FORBIDDEN:
            if phrase in text:
                hits.append({"path": str(path), "phrase": phrase})
    return {"ok": not hits, "hits": hits, "claim_allowed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-root", default="paper")
    parser.add_argument("--out", default="data/results/v7_paper_result_gate.json")
    parser.add_argument("--report", default="docs/V7_PAPER_RESULT_GATE_REPORT.md")
    args = parser.parse_args(argv)
    payload = audit(args.paper_root)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "# V7 Paper Result Gate Report\n\n"
    report += f"Status: `{'PASS' if payload['ok'] else 'BLOCKED'}`\n\n"
    report += "Allowed placeholders: `TBD_AWAITING_REAL_RUNS`.\n"
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report, encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
