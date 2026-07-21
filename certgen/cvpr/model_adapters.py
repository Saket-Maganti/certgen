"""Typed, family-specific model adapters for the real CVPR generation path.

Heavy libraries are imported only inside ``load`` so local contract tests never
download or initialize a model or CUDA runtime.
"""

from __future__ import annotations

import gc
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, NoReturn, Sequence

from PIL import Image


CLAIM_RELEVANT_FIELDS = (
    "batch_size",
    "seeds",
    "num_inference_steps",
    "scheduler",
    "guidance_scale",
    "width",
    "height",
    "prompts",
    "class_ids",
    "precision",
    "output_type",
)


@dataclass(frozen=True)
class AdapterCapabilities:
    supports_batching: bool
    supports_generator_list: bool
    supports_class_conditioning: bool
    supports_prompt_conditioning: bool
    supports_guidance: bool
    supports_scheduler_override: bool
    supports_resolution_override: bool
    supports_mixed_precision: bool
    supports_cpu_load: bool
    supports_gpu_load: bool
    known_limitations: tuple[str, ...] = ()
    lightweight_concurrency: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModelAdapter(ABC):
    adapter_name: str

    @abstractmethod
    def load(self, local_snapshot_path: str | Path, runtime_config: Mapping[str, Any], device: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def validate_config(self, runtime_config: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_smoke(self, runtime_config: Mapping[str, Any]) -> Sequence[Image.Image]:
        raise NotImplementedError

    @abstractmethod
    def generate_batch(self, runtime_config: Mapping[str, Any]) -> Sequence[Image.Image]:
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        raise NotImplementedError


class UnsupportedModelAdapter(ModelAdapter):
    adapter_name = "unsupported"

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def _fail(self) -> NoReturn:
        raise NotImplementedError(self.reason)

    def load(self, local_snapshot_path: str | Path, runtime_config: Mapping[str, Any], device: str) -> None:
        self._fail()

    def validate_config(self, runtime_config: Mapping[str, Any]) -> dict[str, Any]:
        self._fail()

    def generate_smoke(self, runtime_config: Mapping[str, Any]) -> Sequence[Image.Image]:
        self._fail()

    def generate_batch(self, runtime_config: Mapping[str, Any]) -> Sequence[Image.Image]:
        self._fail()

    def unload(self) -> None:
        return None

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(False, False, False, False, False, False, False, False, False, False, (self.reason,))


class DiffusersAdapter(ModelAdapter):
    pipeline_class_name = "DiffusionPipeline"

    def __init__(
        self,
        *,
        adapter_name: str,
        capabilities: AdapterCapabilities,
        loader: Callable[..., Any] | None = None,
        torch_module: Any | None = None,
    ) -> None:
        self.adapter_name = adapter_name
        self._capabilities = capabilities
        self._loader = loader
        self._torch = torch_module
        self.pipeline: Any | None = None
        self.device = "cpu"
        self.applied_record: dict[str, Any] | None = None

    def capabilities(self) -> AdapterCapabilities:
        return self._capabilities

    def validate_config(self, runtime_config: Mapping[str, Any]) -> dict[str, Any]:
        missing = [field for field in CLAIM_RELEVANT_FIELDS if field not in runtime_config]
        if missing:
            raise ValueError("runtime config missing claim-relevant fields: " + ", ".join(missing))
        if int(runtime_config["batch_size"]) <= 0:
            raise ValueError("batch_size must be positive")
        seeds = runtime_config["seeds"]
        if not isinstance(seeds, list) or not seeds or len(seeds) != len(set(seeds)):
            raise ValueError("seeds must be a non-empty duplicate-free list")
        if runtime_config.get("guidance_scale") is not None and not self._capabilities.supports_guidance:
            raise ValueError("adapter cannot apply guidance_scale")
        if runtime_config.get("prompts") and not self._capabilities.supports_prompt_conditioning:
            raise ValueError("adapter cannot apply prompts")
        if runtime_config.get("class_ids") and not self._capabilities.supports_class_conditioning:
            raise ValueError("adapter cannot apply class_ids")
        if runtime_config.get("scheduler") not in {None, "checkpoint_default_pinned"} and not self._capabilities.supports_scheduler_override:
            raise ValueError("adapter cannot apply scheduler override")
        if str(runtime_config["precision"]) not in {"float16", "float32", "bfloat16"}:
            raise ValueError("unsupported precision")
        if str(runtime_config["precision"]) != "float32" and not self._capabilities.supports_mixed_precision:
            raise ValueError("adapter cannot apply mixed precision")
        return {field: runtime_config[field] for field in CLAIM_RELEVANT_FIELDS}

    def load(self, local_snapshot_path: str | Path, runtime_config: Mapping[str, Any], device: str) -> None:
        requested = self.validate_config(runtime_config)
        snapshot = Path(local_snapshot_path)
        if not snapshot.is_dir():
            raise FileNotFoundError(f"local model snapshot missing: {snapshot}")
        torch = self._torch
        if torch is None:
            import torch as imported_torch

            torch = imported_torch
            self._torch = torch
        if self._loader is None:
            from diffusers import DDPMPipeline, DiffusionPipeline  # type: ignore[import-not-found]

            pipeline_class = DDPMPipeline if self.pipeline_class_name == "DDPMPipeline" else DiffusionPipeline
            self._loader = pipeline_class.from_pretrained
        dtype = {
            "float16": torch.float16,
            "float32": torch.float32,
            "bfloat16": torch.bfloat16,
        }[str(runtime_config["precision"])]
        self.pipeline = self._loader(
            str(snapshot),
            local_files_only=True,
            torch_dtype=dtype,
        ).to(device)
        self.device = device
        scheduler_name = type(getattr(self.pipeline, "scheduler", None)).__name__
        applied = dict(requested)
        applied["scheduler"] = scheduler_name
        differences: dict[str, Any] = {}
        requested_scheduler = runtime_config.get("scheduler")
        if requested_scheduler not in {None, "checkpoint_default_pinned", scheduler_name}:
            differences["scheduler"] = {"requested": requested_scheduler, "applied": scheduler_name}
        if not self._capabilities.supports_resolution_override:
            unet = getattr(self.pipeline, "unet", None)
            sample_size = getattr(getattr(unet, "config", None), "sample_size", None)
            if isinstance(sample_size, int):
                actual_width = actual_height = sample_size
            elif isinstance(sample_size, (list, tuple)) and len(sample_size) == 2:
                actual_height, actual_width = int(sample_size[0]), int(sample_size[1])
            else:
                raise ValueError("adapter cannot verify the checkpoint-native output resolution")
            applied["width"] = actual_width
            applied["height"] = actual_height
            for field, actual in (("width", actual_width), ("height", actual_height)):
                if int(runtime_config[field]) != actual:
                    differences[field] = {"requested": int(runtime_config[field]), "applied": actual}
        if differences:
            raise ValueError(f"claim-relevant runtime configuration was not applied: {differences}")
        self.applied_record = {
            "requested_config": requested,
            "applied_config": applied,
            "differences": differences,
            "adapter_name": self.adapter_name,
            "pipeline_class": type(self.pipeline).__name__,
            "scheduler_class": scheduler_name,
            "claim_allowed": False,
        }

    def _generators(self, seeds: Sequence[int]) -> Any:
        if self._torch is None:
            raise RuntimeError("adapter is not loaded")
        generators = [self._torch.Generator(device=self.device).manual_seed(int(seed)) for seed in seeds]
        return generators if self._capabilities.supports_generator_list else generators[0]

    def _call_kwargs(self, config: Mapping[str, Any]) -> dict[str, Any]:
        seeds = [int(seed) for seed in config["seeds"]]
        kwargs: dict[str, Any] = {
            "generator": self._generators(seeds),
            "num_inference_steps": int(config["num_inference_steps"]),
            "output_type": str(config["output_type"]),
        }
        if self._capabilities.supports_batching:
            kwargs["batch_size"] = len(seeds)
        if self._capabilities.supports_resolution_override:
            kwargs.update(width=int(config["width"]), height=int(config["height"]))
        if self._capabilities.supports_prompt_conditioning:
            kwargs["prompt"] = list(config["prompts"])
        if self._capabilities.supports_class_conditioning:
            kwargs["class_labels"] = list(config["class_ids"])
        if self._capabilities.supports_guidance and config.get("guidance_scale") is not None:
            kwargs["guidance_scale"] = float(config["guidance_scale"])
        return kwargs

    def generate_batch(self, runtime_config: Mapping[str, Any]) -> Sequence[Image.Image]:
        self.validate_config(runtime_config)
        if self.pipeline is None:
            raise RuntimeError("adapter must be loaded before generation")
        seeds = list(runtime_config["seeds"])
        if not self._capabilities.supports_generator_list and len(seeds) > 1:
            images: list[Image.Image] = []
            for index, seed in enumerate(seeds):
                micro = dict(runtime_config)
                micro["seeds"] = [seed]
                if micro.get("prompts"):
                    micro["prompts"] = [runtime_config["prompts"][index]]
                if micro.get("class_ids"):
                    micro["class_ids"] = [runtime_config["class_ids"][index]]
                images.extend(self.pipeline(**self._call_kwargs(micro)).images)
            return images
        return list(self.pipeline(**self._call_kwargs(runtime_config)).images)

    def generate_smoke(self, runtime_config: Mapping[str, Any]) -> Sequence[Image.Image]:
        if not 1 <= len(runtime_config["seeds"]) <= 4:
            raise ValueError("smoke generation requires 1-4 seeds")
        return self.generate_batch(runtime_config)

    def unload(self) -> None:
        self.pipeline = None
        gc.collect()
        if self._torch is not None and hasattr(self._torch, "cuda"):
            self._torch.cuda.empty_cache()


UNCONDITIONAL_CAPABILITIES = AdapterCapabilities(
    True, True, False, False, False, False, False, True, True, True,
    ("checkpoint scheduler is retained", "resolution override is not assumed"),
)
TEXT_CAPABILITIES = AdapterCapabilities(True, True, False, True, True, False, True, True, True, True)
CLASS_CAPABILITIES = AdapterCapabilities(True, True, True, False, True, False, True, True, True, True)


class UnconditionalDDPMAdapter(DiffusersAdapter):
    pipeline_class_name = "DDPMPipeline"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(adapter_name="diffusers_unconditional_ddpm", capabilities=UNCONDITIONAL_CAPABILITIES, **kwargs)


class TextToImageAdapter(DiffusersAdapter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(adapter_name="diffusers_text_to_image", capabilities=TEXT_CAPABILITIES, **kwargs)

    def validate_config(self, runtime_config: Mapping[str, Any]) -> dict[str, Any]:
        requested = super().validate_config(runtime_config)
        if len(runtime_config["prompts"]) != len(runtime_config["seeds"]):
            raise ValueError("text-to-image requires exactly one prompt per seed")
        return requested

    def _call_kwargs(self, config: Mapping[str, Any]) -> dict[str, Any]:
        kwargs = super()._call_kwargs(config)
        # Diffusers text pipelines derive the batch from the prompt list;
        # passing an invented ``batch_size`` keyword breaks real pipelines.
        kwargs.pop("batch_size", None)
        return kwargs


class ClassConditionalDiffusionAdapter(DiffusersAdapter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(adapter_name="diffusers_class_conditional", capabilities=CLASS_CAPABILITIES, **kwargs)

    def validate_config(self, runtime_config: Mapping[str, Any]) -> dict[str, Any]:
        requested = super().validate_config(runtime_config)
        if len(runtime_config["class_ids"]) != len(runtime_config["seeds"]):
            raise ValueError("class-conditional generation requires exactly one class ID per seed")
        return requested

    def _call_kwargs(self, config: Mapping[str, Any]) -> dict[str, Any]:
        kwargs = super()._call_kwargs(config)
        # DiT/class-conditional Diffusers pipelines infer the batch from the
        # class-label list, as text pipelines do from prompts.
        kwargs.pop("batch_size", None)
        return kwargs


def adapter_for_model(model: Mapping[str, Any], **kwargs: Any) -> ModelAdapter:
    adapter = str(model.get("adapter", "")).lower()
    family = str(model.get("family", "")).lower()
    conditioning = str(model.get("conditioning", "")).lower()
    if "cfm" in adapter or "flow" in family:
        return UnsupportedModelAdapter(
            "CFM remains blocked: loading, batching, generator, scheduler, and sampler semantics are not validated"
        )
    if conditioning == "unconditional" and ("ddpm" in adapter or "ddpm" in family):
        return UnconditionalDDPMAdapter(**kwargs)
    if conditioning in {"text", "prompt", "text_to_image"} and (
        "diffusers" in adapter or "pipeline" in adapter
    ) and "tbd" not in adapter:
        return TextToImageAdapter(**kwargs)
    if conditioning in {"class", "class_conditional", "conditional"} and (
        "ditpipeline" in adapter or "class_conditional" in adapter
    ):
        return ClassConditionalDiffusionAdapter(**kwargs)
    return UnsupportedModelAdapter(f"no validated adapter for model {model.get('model_id', '<unknown>')}")
