"""CLI for certificate replay."""

from __future__ import annotations

import argparse

from certgen.certs.replay import replay_certificate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay a V3 certificate.")
    parser.add_argument("--certificate", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = replay_certificate(args.certificate, args.out, args.json_out)
    print(f"Certificate replay status: {payload['replay_status']}")
    return 0 if payload["replay_status"] in {"passed", "blocked_missing_inputs"} else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
