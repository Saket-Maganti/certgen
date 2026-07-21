"""Guarded CIFAR-10 sample generation for selected Diffusers checkpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import write_json


KNOWN_CHECKPOINTS: dict[str, dict[str, Any]] = {
    "google/ddpm-cifar10-32": {
        "adapter_status": "ready_guarded_diffusers_ddpm_pipeline",
        "pipeline_class": "DDPMPipeline",
        "revision": "267b167dc01f0e4e61923ea244e8b988f84deb80",
        "expected_resolution": "32x32_rgb",
    },
    "FrankCCCCC/ddpm_ema_cifar10": {
        "adapter_status": "ready_guarded_diffusers_ddpm_pipeline",
        "pipeline_class": "DDPMPipeline",
        "revision": "6aa387f240fbb00d0e003f93a3b994f56dd98dc2",
        "expected_resolution": "32x32_rgb",
    },
    "FrankCCCCC/cfm-cifar10-32": {
        "adapter_status": "ready_guarded_diffusers_ddpm_pipeline_per_model_card",
        "pipeline_class": "DDPMPipeline",
        "revision": "b3f30358497e11ce5011c00614c9b0521262f51c",
        "expected_resolution": "32x32_rgb",
        "note": "Flow-matching checkpoint uses DDPMPipeline per model card; execute mode remains a real-run validation gate.",
    },
}


def checkpoint_adapter_statuses() -> dict[str, dict[str, Any]]:
    return {key: dict(value) for key, value in KNOWN_CHECKPOINTS.items()}


def _slug(checkpoint_id: str) -> str:
    return checkpoint_id.replace("/", "__").replace("-", "_")


def _planned_seeds(seed_start: int, seed_end: int | None, num_samples: int | None) -> list[int]:
    if num_samples is None and seed_end is None:
        raise ValueError("set --num-samples or --seed-end")
    if num_samples is not None and num_samples <= 0:
        raise ValueError("--num-samples must be positive")
    if seed_end is None:
        seed_end = seed_start + int(num_samples)
    if seed_end <= seed_start:
        raise ValueError("--seed-end must be greater than --seed-start")
    seeds = list(range(seed_start, seed_end))
    if num_samples is not None:
        seeds = seeds[:num_samples]
    return seeds


def _image_shape(image: Any) -> tuple[int, int, int]:
    width, height = image.size
    try:
        channels = len(image.getbands())
    except Exception:
        channels = 3
    return int(width), int(height), int(channels)


def _write_manifest(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _manifest_row(
    *,
    checkpoint_id: str,
    seed: int,
    image_path: Path,
    width: int,
    height: int,
    channels: int,
    generation_status: str,
    adapter_status: str,
    device: str,
    checkpoint_revision: str | None = None,
) -> dict[str, Any]:
    image_hash = file_sha256(image_path) if image_path.exists() else None
    sample_id = f"{_slug(checkpoint_id)}_seed_{seed:08d}"
    return {
        "sample_id": sample_id,
        "checkpoint_id": checkpoint_id,
        "checkpoint_revision": checkpoint_revision,
        "model_id": checkpoint_id,
        "seed": seed,
        "image_path": str(image_path),
        "path": str(image_path),
        "image_hash": image_hash,
        "sha256": image_hash,
        "width": width,
        "height": height,
        "channels": channels,
        "generation_status": generation_status,
        "adapter_status": adapter_status,
        "device": device,
        "source_type": "checkpoint_generated",
        "evidence_status": "r1a_sample_package_non_evidence",
        "claim_allowed": False,
    }


def plan_generation(
    *,
    checkpoint_id: str,
    seed_start: int,
    seed_end: int | None,
    num_samples: int | None,
    out_dir: str | Path,
    manifest_out: str | Path,
    device: str,
    batch_size: int,
    allow_unknown_checkpoint: bool = False,
) -> dict[str, Any]:
    if checkpoint_id not in KNOWN_CHECKPOINTS and not allow_unknown_checkpoint:
        raise ValueError(f"unknown checkpoint_id blocked: {checkpoint_id}")
    seeds = _planned_seeds(seed_start, seed_end, num_samples)
    checkpoint = KNOWN_CHECKPOINTS.get(
        checkpoint_id,
        {"adapter_status": "blocked_unknown_checkpoint_explicitly_allowed_for_planning_only", "pipeline_class": "unknown"},
    )
    return {
        "checkpoint_id": checkpoint_id,
        "checkpoint_config": checkpoint,
        "seed_start": seed_start,
        "seed_end": seeds[-1] + 1 if seeds else seed_start,
        "num_samples": len(seeds),
        "out_dir": str(out_dir),
        "manifest_out": str(manifest_out),
        "device": device,
        "batch_size": batch_size,
        "execute": False,
        "evidence_status": "r1a_generation_plan_only",
        "claim_allowed": False,
        "plan_hash": stable_hash_json({"checkpoint_id": checkpoint_id, "seeds": seeds, "out_dir": str(out_dir)}),
    }


def run_generation(
    *,
    checkpoint_id: str,
    seed_start: int,
    seed_end: int | None,
    num_samples: int | None,
    out_dir: str | Path,
    manifest_out: str | Path,
    device: str,
    batch_size: int,
    resume: bool,
    execute: bool,
    dry_run: bool,
    allow_unknown_checkpoint: bool = False,
    json_out: str | Path | None = None,
) -> dict[str, Any]:
    if not execute:
        if not dry_run:
            raise PermissionError("sample generation refuses to run without --execute; use --dry-run for a plan")
        plan = plan_generation(
            checkpoint_id=checkpoint_id,
            seed_start=seed_start,
            seed_end=seed_end,
            num_samples=num_samples,
            out_dir=out_dir,
            manifest_out=manifest_out,
            device=device,
            batch_size=batch_size,
            allow_unknown_checkpoint=allow_unknown_checkpoint,
        )
        if json_out:
            write_json(plan, json_out)
        return plan
    if checkpoint_id not in KNOWN_CHECKPOINTS:
        raise ValueError(f"unknown checkpoint_id blocked: {checkpoint_id}")

    try:
        import torch
        from diffusers import DDPMPipeline
    except Exception as exc:  # pragma: no cover - real-run dependency path.
        raise RuntimeError("execute mode requires torch and diffusers") from exc

    seeds = _planned_seeds(seed_start, seed_end, num_samples)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = KNOWN_CHECKPOINTS[checkpoint_id]
    pipe = DDPMPipeline.from_pretrained(checkpoint_id, revision=str(checkpoint["revision"]))
    if hasattr(pipe, "to"):
        pipe = pipe.to(device)

    rows: list[dict[str, Any]] = []
    for offset in range(0, len(seeds), max(1, batch_size)):
        batch_seeds = seeds[offset : offset + max(1, batch_size)]
        generators = [torch.Generator(device=device).manual_seed(seed) for seed in batch_seeds]
        outputs = pipe(batch_size=len(batch_seeds), generator=generators)
        images = outputs.images
        for seed, image in zip(batch_seeds, images):
            image_path = out_dir / f"{_slug(checkpoint_id)}_seed_{seed:08d}.png"
            if image_path.exists() and not resume:
                raise FileExistsError(f"generated image exists and --resume was not set: {image_path}")
            if not image_path.exists():
                image.save(image_path)
            width, height, channels = _image_shape(image)
            rows.append(
                _manifest_row(
                    checkpoint_id=checkpoint_id,
                    seed=seed,
                    image_path=image_path,
                    width=width,
                    height=height,
                    channels=channels,
                    generation_status="generated",
                    adapter_status=str(checkpoint["adapter_status"]),
                    device=device,
                    checkpoint_revision=str(checkpoint["revision"]),
                )
            )
    _write_manifest(rows, Path(manifest_out))
    summary = {
        "checkpoint_id": checkpoint_id,
        "checkpoint_revision": checkpoint["revision"],
        "num_samples": len(rows),
        "manifest_out": str(manifest_out),
        "out_dir": str(out_dir),
        "execute": True,
        "evidence_status": "r1a_sample_package_non_evidence",
        "claim_allowed": False,
    }
    if json_out:
        write_json(summary, json_out)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate CIFAR-10 samples from guarded Diffusers checkpoints.")
    parser.add_argument("--checkpoint-id", required=True)
    parser.add_argument("--seed-start", type=int, required=True)
    parser.add_argument("--seed-end", type=int)
    parser.add_argument("--num-samples", type=int)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--device", choices=["cuda", "cpu"], required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-unknown-checkpoint", action="store_true")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    try:
        result = run_generation(
            checkpoint_id=args.checkpoint_id,
            seed_start=args.seed_start,
            seed_end=args.seed_end,
            num_samples=args.num_samples,
            out_dir=args.out_dir,
            manifest_out=args.manifest_out,
            device=args.device,
            batch_size=args.batch_size,
            resume=args.resume,
            execute=args.execute,
            dry_run=args.dry_run,
            allow_unknown_checkpoint=args.allow_unknown_checkpoint,
            json_out=args.json_out,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    mode = "executed" if args.execute else "planned"
    print(f"{mode} {result['num_samples']} samples for {args.checkpoint_id}; claim_allowed=False")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
