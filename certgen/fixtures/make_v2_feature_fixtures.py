"""Create deterministic synthetic V2 feature fixtures."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json


def make_v2_feature_fixtures(out_dir: str | Path, seed: int = 0, n: int = 80, d: int = 6) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    reference = rng.normal(0.0, 0.05, size=(n, d))
    arrays = {
        "reference": reference,
        "model_a_close": reference + rng.normal(0.0, 0.015, size=(n, d)),
        "model_b_far": reference + 0.70 + rng.normal(0.0, 0.02, size=(n, d)),
        "model_a_far": reference - 0.70 + rng.normal(0.0, 0.02, size=(n, d)),
        "model_b_close": reference + rng.normal(0.0, 0.015, size=(n, d)),
        "model_equal_1": reference + rng.normal(0.0, 0.02, size=(n, d)),
        "model_equal_2": reference + rng.normal(0.0, 0.02, size=(n, d)),
    }
    paths: dict[str, str] = {}
    for name, array in arrays.items():
        path = out / f"{name}.npz"
        np.savez_compressed(path, features=array.astype(np.float64))
        meta = {
            "fixture_id": name,
            "evidence_status": "smoke_only",
            "warning": "NO_REAL_EVIDENCE: synthetic fixture for software validation only",
            "seed": seed,
            "num_samples": n,
            "feature_dim": d,
            "feature_file_path": str(path),
            "feature_file_sha256": file_sha256(path),
        }
        write_json(meta, out / f"{name}.metadata.json")
        paths[name] = str(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate V2 smoke feature fixtures.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    paths = make_v2_feature_fixtures(args.out_dir, seed=args.seed)
    print(f"Wrote {len(paths)} V2 smoke feature fixtures to {args.out_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
