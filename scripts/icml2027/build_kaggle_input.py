#!/usr/bin/env python3
"""CLI wrapper for deterministic ICML 2027 Kaggle input builders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from certgen.icml2027.kaggle import build_input, compute_prerequisite_identity  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", required=True)
    parser.add_argument("--input", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--out-root", default="artifacts/icml2027/kaggle_inputs")
    parser.add_argument("--prerequisite-identity-only", action="store_true")
    args = parser.parse_args()
    inputs: dict[str, str | Path] = {}
    for item in args.input:
        if "=" not in item:
            parser.error("--input must use NAME=PATH")
        name, value = item.split("=", 1)
        if name in inputs:
            parser.error(f"duplicate input name: {name}")
        inputs[name] = value
    if args.prerequisite_identity_only:
        payload = {
            "lane": args.lane,
            "authenticated_prerequisite_set_sha256": compute_prerequisite_identity(args.lane, inputs),
            "claim_allowed": False,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = build_input(args.lane, inputs, root=WORKSPACE_ROOT, out_root=args.out_root)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("input_zip_created") else 3


if __name__ == "__main__":
    raise SystemExit(main())
