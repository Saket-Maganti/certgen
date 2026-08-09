"""Prospective preprocessing-ablation contracts separate from confirmatory inputs."""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

from certgen.icml2027.common import stable_hash, write_csv, write_json


ABLATIONS: dict[str, list[object]] = {
    "interpolation": ["bilinear", "bicubic"],
    "antialias": [True, False],
    "spatial_policy": ["center_crop", "resize_only"],
    "pixel_normalization": ["extractor_default", "unit_interval", "minus_one_to_one"],
    "feature_l2": [True, False],
    "metric_dtype": ["float32", "float64"],
}


def build_ablation_matrix(out_path: str | Path) -> dict[str, Any]:
    keys = list(ABLATIONS)
    rows: list[dict[str, Any]] = []
    for index, values in enumerate(itertools.product(*(ABLATIONS[key] for key in keys))):
        settings = dict(zip(keys, values, strict=True))
        rows.append(
            {
                "ablation_id": f"preprocess_{index:03d}",
                **settings,
                "preprocessing_hash": stable_hash(settings),
                "registered_ablation_only": True,
                "confirmatory_protocol_mutated": False,
                "planning_only": True,
                "claim_allowed": False,
            }
        )
    target = Path(out_path)
    write_csv(target, rows)
    summary = {
        "schema_version": "certgen.icml2027.preprocessing_ablation_matrix.v1",
        "rows": len(rows),
        "factors": ABLATIONS,
        "confirmatory_protocol_mutated": False,
        "planning_only": True,
        "claim_allowed": False,
    }
    write_json(target.with_suffix(".json"), summary)
    return summary
