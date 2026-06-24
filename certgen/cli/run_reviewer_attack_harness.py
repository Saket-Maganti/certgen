"""Run reviewer attack harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.review.attacks import attack_cards
from certgen.review.score_simulator import simulate_scorecard


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V4 reviewer attack harness.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    cards = attack_cards()
    payload = {"attacks": cards, "scorecard": simulate_scorecard(), "claim_allowed": False}
    lines = ["# Reviewer Attacks V4", "", "`NO_REAL_EVIDENCE`", ""]
    for card in cards:
        lines.append(f"- **{card['attack_id']}** {card['attack']} Status: `{card['current_status']}`")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, args.json_out)
    print(f"Wrote reviewer attack harness: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
