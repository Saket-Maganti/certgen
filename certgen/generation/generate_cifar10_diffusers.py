"""Guarded CIFAR-10 sample generation for selected Diffusers checkpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

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
        if num_samples is None:  # narrowed explicitly for static analyzers
            raise AssertionError("num_samples is required when seed_end is absent")
        seed_end = seed_start + num_samples
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
    sample_id: str | None = None,
    sample_index: int | None = None,
    asset_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    image_hash = file_sha256(image_path) if image_path.exists() else None
    sample_id = sample_id or f"{_slug(checkpoint_id)}_seed_{seed:08d}"
    return {
        "sample_id": sample_id,
        "sample_index": sample_index,
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
        "authenticated_asset_identity": dict(asset_identity or {}),
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
        from diffusers import DDPMPipeline  # type: ignore[import-not-found]
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


def run_generation_samples(
    *,
    checkpoint_id: str,
    samples: list[dict[str, Any]],
    out_dir: str | Path,
    manifest_out: str | Path,
    device: str,
    batch_size: int,
    resume: bool,
    authenticated_snapshot_root: str | Path,
    asset_identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Generate the exact authenticated sample-ID/RNG-seed records for one shard."""

    if checkpoint_id not in KNOWN_CHECKPOINTS:
        raise ValueError(f"unknown checkpoint_id blocked: {checkpoint_id}")
    if not samples:
        raise ValueError("the frozen seed-record shard must be non-empty")
    sample_ids = [str(row.get("sample_id", "")) for row in samples]
    generator_seeds = [int(row.get("generator_seed", -1)) for row in samples]
    sample_indices = [int(row.get("sample_index", -1)) for row in samples]
    if any(not value or "/" in value or ".." in value for value in sample_ids):
        raise ValueError("unsafe or empty frozen sample ID")
    if len(sample_ids) != len(set(sample_ids)) or len(generator_seeds) != len(set(generator_seeds)):
        raise ValueError("duplicate sample ID or generator seed in authenticated shard")
    if generator_seeds != [int(row["generator_seed"]) for row in samples] or any(seed < 0 or seed >= 2**63 for seed in generator_seeds):
        raise ValueError("generator seed is outside the frozen signed-64-bit range")
    checkpoint = KNOWN_CHECKPOINTS[checkpoint_id]
    snapshot_root = Path(authenticated_snapshot_root).resolve()
    if not snapshot_root.is_dir() or Path(authenticated_snapshot_root).is_symlink():
        raise ValueError("authenticated generator snapshot root is missing or symlinked")
    if (
        asset_identity.get("model_identifier") != checkpoint_id
        or asset_identity.get("revision") != checkpoint["revision"]
        or asset_identity.get("local_files_only") is not True
        or asset_identity.get("loader_type") != "from_pretrained_local_snapshot"
    ):
        raise ValueError("authenticated generator asset identity mismatch")
    for field in (
        "aggregate_manifest_sha256",
        "asset_manifest_sha256",
        "inventory_sha256",
    ):
        if not isinstance(asset_identity.get(field), str) or len(str(asset_identity.get(field))) != 64:
            raise ValueError(f"authenticated generator asset is missing {field}")
    for row in samples:
        if row.get("checkpoint_id") != checkpoint_id or row.get("checkpoint_revision") != checkpoint["revision"]:
            raise ValueError("frozen seed record checkpoint identity mismatch")
        if row.get("claim_allowed") is not False:
            raise ValueError("claim_allowed must remain false")
    try:
        import torch
        from diffusers import DDPMPipeline  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - authenticated GPU path.
        raise RuntimeError("execute mode requires torch and diffusers") from exc
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_target = Path(manifest_out)
    completed: dict[str, dict[str, Any]] = {}
    if resume and manifest_target.is_file():
        for line in manifest_target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                prior = json.loads(line)
                completed[str(prior["sample_id"])] = prior
    pipe = DDPMPipeline.from_pretrained(str(snapshot_root), local_files_only=True)
    if hasattr(pipe, "to"):
        pipe = pipe.to(device)
    rows: list[dict[str, Any]] = []
    width = height = channels = 0
    for offset in range(0, len(samples), max(1, batch_size)):
        batch = samples[offset : offset + max(1, batch_size)]
        pending = []
        for row in batch:
            image_path = target / f"{row['sample_id']}.png"
            if not image_path.is_file():
                pending.append(row)
                continue
            if not resume:
                raise FileExistsError("generated image exists and resume was not set")
            prior = completed.get(str(row["sample_id"]))
            if (
                prior is None
                or prior.get("seed") != row["generator_seed"]
                or prior.get("checkpoint_id") != checkpoint_id
                or prior.get("checkpoint_revision") != checkpoint["revision"]
                or prior.get("image_hash") != file_sha256(image_path)
            ):
                raise RuntimeError("stale or corrupt generation shard rejected; quarantine and rerun the shard")
        generated: dict[str, Any] = {}
        if pending:
            generators = [
                torch.Generator(device=device).manual_seed(int(row["generator_seed"])) for row in pending
            ]
            outputs = pipe(batch_size=len(pending), generator=generators)
            generated = {str(row["sample_id"]): image for row, image in zip(pending, outputs.images, strict=True)}
        for row in batch:
            sample_id = str(row["sample_id"])
            image_path = target / f"{sample_id}.png"
            image = generated.get(sample_id)
            if image is not None:
                image.save(image_path)
                width, height, channels = _image_shape(image)
            else:
                from PIL import Image

                with Image.open(image_path) as saved:
                    saved.verify()
                with Image.open(image_path) as saved:
                    width, height, channels = _image_shape(saved)
            rows.append(
                _manifest_row(
                    checkpoint_id=checkpoint_id,
                    seed=int(row["generator_seed"]),
                    image_path=image_path,
                    width=width,
                    height=height,
                    channels=channels,
                    generation_status="generated",
                    adapter_status=str(checkpoint["adapter_status"]),
                    device=device,
                    checkpoint_revision=str(checkpoint["revision"]),
                    sample_id=sample_id,
                    sample_index=int(row["sample_index"]),
                    asset_identity=asset_identity,
                )
            )
    rows.sort(key=lambda row: int(row["sample_index"]))
    _write_manifest(rows, manifest_target)
    return {
        "checkpoint_id": checkpoint_id,
        "checkpoint_revision": checkpoint["revision"],
        "num_samples": len(rows),
        "sample_index_start": min(sample_indices),
        "sample_index_stop": max(sample_indices) + 1,
        "seed_records_sha256": stable_hash_json(samples),
        "manifest_out": str(manifest_out),
        "out_dir": str(out_dir),
        "execute": True,
        "authenticated_snapshot_root_runtime_only": str(snapshot_root),
        "authenticated_asset_identity": dict(asset_identity),
        "local_files_only": True,
        "claim_allowed": False,
    }


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
