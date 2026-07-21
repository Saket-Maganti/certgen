"""Deterministic batched generation with adaptive OOM and atomic batches."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from PIL import Image

from certgen.cvpr.contracts import atomic_write_json


class BatchAdapter(Protocol):
    supports_generator_list: bool

    def generate(self, *, seeds: Sequence[int], prompts: Sequence[str | None]) -> Sequence[Image.Image]: ...

    def clear_cache(self) -> None: ...


@dataclass(frozen=True)
class GenerationSample:
    sample_id: str
    seed: int
    prompt_or_label: str | None = None


@dataclass(frozen=True)
class GenerationSettings:
    model_id: str
    scheduler: str
    inference_steps: int
    guidance_scale: float | None
    precision: str
    device: str
    configured_batch_size: int
    minimum_batch_size: int = 1
    image_size: tuple[int, int] = (32, 32)
    image_mode: str = "RGB"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_replace_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _is_oom(error: BaseException) -> bool:
    text = str(error).lower()
    return "out of memory" in text or "cuda oom" in text


def _validate_samples(samples: Sequence[GenerationSample]) -> None:
    sample_ids = [sample.sample_id for sample in samples]
    seeds = [sample.seed for sample in samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("duplicate sample IDs are forbidden")
    if len(seeds) != len(set(seeds)):
        raise ValueError("duplicate seeds are forbidden")
    if any(not sample_id or "/" in sample_id or ".." in sample_id for sample_id in sample_ids):
        raise ValueError("unsafe sample ID")


def _completed_samples(output_root: Path, configuration_hash: str) -> dict[str, str]:
    completed: dict[str, str] = {}
    for path in sorted((output_root / "batches").glob("*/batch_manifest.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != "COMPLETE" or payload.get("configuration_hash") != configuration_hash:
            raise ValueError(f"conflicting batch manifest: {path}")
        for row in payload.get("images", []):
            image = output_root / row["relative_image_path"]
            if not image.is_file() or _sha256(image) != row["image_hash"]:
                raise ValueError(f"completed image hash conflict: {image}")
            sample_id = str(row["sample_id"])
            if sample_id in completed and completed[sample_id] != row["image_hash"]:
                raise ValueError(f"duplicate completed sample conflict: {sample_id}")
            completed[sample_id] = row["image_hash"]
    return completed


def generate_batches(
    *,
    adapter: BatchAdapter,
    samples: Sequence[GenerationSample],
    settings: GenerationSettings,
    output_root: str | Path,
    configuration_hash: str,
    resume: bool,
) -> dict[str, Any]:
    _validate_samples(samples)
    if settings.minimum_batch_size < 1 or settings.configured_batch_size < settings.minimum_batch_size:
        raise ValueError("invalid batch-size bounds")
    out = Path(output_root)
    images_root = out / "images"
    batches_root = out / "batches"
    temporary_root = out / ".partial_batches"
    for path in (images_root, batches_root, temporary_root):
        path.mkdir(parents=True, exist_ok=True)
    completed = _completed_samples(out, configuration_hash) if resume else {}
    pending = [sample for sample in samples if sample.sample_id not in completed]
    if not resume and any(batches_root.iterdir()):
        raise FileExistsError("existing batches require resume mode")

    batch_size = settings.configured_batch_size
    oom_events = 0
    batch_rows: list[dict[str, Any]] = []
    cursor = 0
    batch_index = len(list(batches_root.glob("*/batch_manifest.json")))
    while cursor < len(pending):
        current = pending[cursor : cursor + batch_size]
        batch_id = f"batch_{batch_index:06d}"
        start_time = time.time()
        try:
            generated = list(
                adapter.generate(
                    seeds=[sample.seed for sample in current],
                    prompts=[sample.prompt_or_label for sample in current],
                )
            )
        except Exception as error:
            if not _is_oom(error):
                raise
            oom_events += 1
            adapter.clear_cache()
            if batch_size <= settings.minimum_batch_size:
                raise RuntimeError("minimum generation batch size also exhausted GPU memory") from error
            batch_size = max(settings.minimum_batch_size, batch_size // 2)
            continue
        if len(generated) != len(current):
            raise ValueError("adapter returned a different image count than the requested batch")

        temporary = temporary_root / batch_id
        if temporary.exists():
            shutil.rmtree(temporary)
        temporary.mkdir()
        image_rows: list[dict[str, Any]] = []
        for sample, image in zip(current, generated, strict=True):
            if image.mode != settings.image_mode or image.size != settings.image_size:
                raise ValueError(f"generated image contract mismatch for {sample.sample_id}")
            temporary_image = temporary / f"{sample.sample_id}.png"
            image.save(temporary_image, format="PNG")
            with Image.open(temporary_image) as decoded:
                decoded.load()
                if decoded.mode != settings.image_mode or decoded.size != settings.image_size:
                    raise ValueError(f"saved image decode mismatch for {sample.sample_id}")
            image_rows.append(
                {
                    "sample_id": sample.sample_id,
                    "role": "model",
                    "model_id": settings.model_id,
                    "relative_image_path": f"images/{sample.sample_id}.png",
                    "image_hash": _sha256(temporary_image),
                    "seed": sample.seed,
                    "prompt_or_class_id": sample.prompt_or_label,
                    "width": settings.image_size[0],
                    "height": settings.image_size[1],
                    "mode": settings.image_mode,
                    "source_run_id": f"{settings.model_id}:generation",
                    "source_manifest_hash": configuration_hash,
                }
            )

        for row in image_rows:
            destination = out / row["relative_image_path"]
            source = temporary / destination.name
            if destination.exists() and _sha256(destination) != row["image_hash"]:
                raise ValueError(f"conflicting existing image: {destination}")
            source.replace(destination)
        shutil.rmtree(temporary)
        end_time = time.time()
        manifest = {
            "schema_version": "certgen.generation_batch.v1",
            "batch_id": batch_id,
            "sample_ids": [sample.sample_id for sample in current],
            "seeds": [sample.seed for sample in current],
            "prompts_or_labels": [sample.prompt_or_label for sample in current],
            "model_id": settings.model_id,
            "scheduler": settings.scheduler,
            "inference_steps": settings.inference_steps,
            "guidance_scale": settings.guidance_scale,
            "precision": settings.precision,
            "device": settings.device,
            "start_time": start_time,
            "end_time": end_time,
            "status": "COMPLETE",
            "configuration_hash": configuration_hash,
            "configured_batch_size": settings.configured_batch_size,
            "effective_batch_size": len(current),
            "OOM_events": oom_events,
            "fallback_reason": "adaptive_OOM_halving" if oom_events else (
                "adapter_generator_list_unsupported_microbatch" if not adapter.supports_generator_list else None
            ),
            "images": image_rows,
            "evidence_class": "run_log_only",
            "claim_allowed": False,
        }
        batch_dir = batches_root / batch_id
        batch_dir.mkdir()
        atomic_write_json(manifest, batch_dir / "batch_manifest.json")
        batch_rows.append(manifest)
        cursor += len(current)
        batch_index += 1

    payload = {
        "status": "COMPLETE",
        "configuration_hash": configuration_hash,
        "configured_batch_size": settings.configured_batch_size,
        "effective_batch_size": batch_size,
        "OOM_events": oom_events,
        "completed_before_resume": len(completed),
        "generated_now": len(pending),
        "total_samples": len(samples),
        "batches": [row["batch_id"] for row in batch_rows],
        "evidence_class": "run_log_only",
        "claim_allowed": False,
    }
    _atomic_replace_json(payload, out / "generation_status.json")
    return payload


class FixtureBatchAdapter:
    """Deterministic tiny adapter used by local runtime-contract tests."""

    supports_generator_list = True

    def __init__(self, *, size: tuple[int, int] = (8, 8), oom_above: int | None = None) -> None:
        self.size = size
        self.oom_above = oom_above
        self.clears = 0

    def generate(self, *, seeds: Sequence[int], prompts: Sequence[str | None]) -> Sequence[Image.Image]:
        if self.oom_above is not None and len(seeds) > self.oom_above:
            raise RuntimeError("CUDA out of memory (fixture injection)")
        return [
            Image.new("RGB", self.size, (seed % 256, (seed // 2) % 256, (seed // 3) % 256))
            for seed in seeds
        ]

    def clear_cache(self) -> None:
        self.clears += 1
