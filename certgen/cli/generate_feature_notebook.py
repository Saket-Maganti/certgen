"""CLI for V4 feature notebook generation."""

from __future__ import annotations

import argparse

from certgen.notebooks.generate_feature_notebook import generate_feature_notebook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a safe feature-extraction notebook script.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--target", required=True, choices=["kaggle", "colab", "local"])
    parser.add_argument("--feature-extractor", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    generate_feature_notebook(args.plan, args.target, args.feature_extractor, args.out)
    print(f"Wrote feature notebook script: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
