"""Run real feature extraction end-to-end (Inception / CLIP / DINOv2).

Safety: actually loading models and writing feature caches requires the explicit
``--execute`` flag. Without it, the CLI resolves and prints the plan only, so this
command is safe to wire into runbooks before the first real pilot. Output caches
are always ``claim_allowed=false`` and ``real_features_unvalidated`` -- promotion
to evidence is a separate cache-validation and metric-reproduction gate.
"""

from __future__ import annotations

import argparse

from certgen.core.io import read_json, write_json
from certgen.features.extractors import EXTRACTORS


def run_feature_extraction(
    *,
    input_manifest: str,
    extractor: str,
    out_dir: str,
    device: str = "auto",
    batch_size: int = 32,
    model_id: str | None = None,
    preprocessing_lock: str | None = None,
    asset_context: dict | None = None,
    max_items: int | None = None,
    execute: bool = False,
    json_out: str | None = None,
) -> dict:
    if extractor not in EXTRACTORS:
        raise ValueError(f"unknown extractor: {extractor}")
    adapter = EXTRACTORS[extractor]()
    preprocessing = read_json(preprocessing_lock) if preprocessing_lock else {}

    if not execute:
        plan = adapter.dry_run_plan(input_manifest, out_dir, batch_size, device)
        plan["requested_model_id"] = model_id
        plan["preprocessing_lock"] = preprocessing_lock
        plan["execute"] = False
        plan["note"] = "pass --execute to perform real extraction"
        if json_out:
            write_json(plan, json_out)
        return plan

    result = adapter.extract(
        input_manifest,
        out_dir,
        batch_size,
        device,
        max_items=max_items,
        model_id=model_id,
        preprocessing=preprocessing,
        asset_context=asset_context,
    )
    if json_out:
        write_json(result, json_out)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run real feature extraction (guarded by --execute).")
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--extractor", required=True, choices=sorted(EXTRACTORS))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--preprocessing-lock", default=None)
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--execute", action="store_true", help="perform real extraction instead of planning only")
    args = parser.parse_args(argv)
    try:
        result = run_feature_extraction(
            input_manifest=args.input_manifest,
            extractor=args.extractor,
            out_dir=args.out_dir,
            device=args.device,
            batch_size=args.batch_size,
            model_id=args.model_id,
            preprocessing_lock=args.preprocessing_lock,
            max_items=args.max_items,
            execute=args.execute,
            json_out=args.json_out,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if args.execute:
        print(f"Extracted {result['num_items']} x {result['feature_dim']} features -> {result['feature_path']}")
    else:
        print(f"Planned extraction for `{args.extractor}` ({result['item_count']} items); pass --execute to run.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
