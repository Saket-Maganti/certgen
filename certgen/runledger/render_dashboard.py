from __future__ import annotations

import argparse
from pathlib import Path

from certgen.runledger.ledger import read_events, render_dashboard


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default="data/results/v7_run_ledger.jsonl")
    parser.add_argument("--out", default="docs/V7_EXECUTION_DASHBOARD.md")
    args = parser.parse_args(argv)
    text = render_dashboard(read_events(args.ledger))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
