"""Create a preprocessing lock."""

from __future__ import annotations

import argparse

from certgen.preprocess.locks import make_preprocessing_lock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a V4 preprocessing lock.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--feature-extractor", default="inception_v3_pool3")
    args = parser.parse_args(argv)
    make_preprocessing_lock(args.name, args.out, feature_extractor=args.feature_extractor)
    print(f"Wrote preprocessing lock: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
