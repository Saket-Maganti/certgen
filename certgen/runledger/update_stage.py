from __future__ import annotations

import argparse

from certgen.runledger.ledger import LedgerEvent, append_event


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default="data/results/v7_run_ledger.jsonl")
    parser.add_argument("--stage", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--blocker-code", default=None)
    parser.add_argument("--evidence-status", default="NO_REAL_EVIDENCE")
    parser.add_argument("--notes", default="")
    args = parser.parse_args(argv)
    append_event(
        args.ledger,
        LedgerEvent(
            stage=args.stage,
            command=args.command,
            status=args.status,
            blocker_code=args.blocker_code,
            evidence_status=args.evidence_status,
            notes=args.notes,
        ),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
