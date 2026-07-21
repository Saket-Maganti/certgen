"""Placeholder for model-specific sample generation.

Prefer released samples. Generation must be implemented per checkpoint with
license, config, seed, and preprocessing provenance before it can produce
CertGen inputs.
"""

from __future__ import annotations

import argparse


MESSAGE = "Sample generation is not implemented. Use released samples or implement model-specific generator with provenance first."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Placeholder CertGen sample generation command.")
    parser.add_argument("--checkpoint")
    parser.add_argument("--config")
    parser.add_argument("--dataset")
    parser.add_argument("--seed-start", type=int)
    parser.add_argument("--seed-end", type=int)
    parser.add_argument("--out-dir")
    parser.add_argument("--manifest-out")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.parse_args(argv)
    print(MESSAGE)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
