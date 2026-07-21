from __future__ import annotations

import argparse
import json
from pathlib import Path

from certgen.generation.checkpoint_adapters import CHECKPOINT_IDS, preflight_checkpoint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/results/v7_checkpoint_preflight_status.json")
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args(argv)
    payload = {
        "checkpoints": [
            preflight_checkpoint(checkpoint, allow_download=args.allow_download).asdict()
            for checkpoint in CHECKPOINT_IDS
        ],
        "claim_allowed": False,
        "evidence_status": "run_log_only",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
