"""Dedicated, offline-bound extractor adapters used by preflight and extraction."""

from __future__ import annotations

import importlib.metadata
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from certgen.core.hashing import file_sha256
from certgen.notebooks.model_assets import (
    AssetPolicy,
    AssetRequirement,
    inventory_cache,
    resolve_local_snapshot,
    validate_asset_identity,
    validate_asset_manifest,
)
from certgen.notebooks.preprocessing_contract import (
    compare_preprocessing,
    normalize_contract,
    observe_inception_contract,
    observe_transformers_processor,
)


@dataclass(frozen=True)
class ExtractorOutputDefinition:
    extractor_id: str
    model_class: str
    processor_class: str
    feature_definition: str
    pre_normalization_dimension: int
    post_normalization_dimension: int
    projection_applied: bool
    l2_normalization_applied: bool
    expected_output_dimension: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExtractorAdapter:
    adapter_id = "base"

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.config = dict(config)
        self.model: Any | None = None
        self.processor: Any | None = None
        self.device: str | None = None
        self.snapshot_path: Path | None = None

    @property
    def extractor_id(self) -> str:
        return str(self.config["feature_space_id"])

    def output_definition(self) -> dict[str, Any]:
        raise NotImplementedError

    def requested_contract(self) -> dict[str, Any]:
        expected = self.config.get("expected_preprocessing")
        if not isinstance(expected, Mapping):
            raise ValueError(f"{self.extractor_id}: expected_preprocessing is missing")
        return {
            "preprocessing": normalize_contract(expected),
            "output_definition": self.output_definition(),
            "claim_allowed": False,
        }

    def validate_asset(self, manifest: Mapping[str, Any], cache_root: str | Path) -> Path:
        validate_asset_manifest(manifest, cache_root=cache_root)
        validate_asset_identity(
            manifest,
            model_or_extractor_id=self.extractor_id,
            revision=str(self.config["revision"]),
        )
        if manifest.get("preflight_status") != "ASSET_VALIDATED":
            raise ValueError("extractor asset manifest has not passed preflight validation")
        snapshot = resolve_local_snapshot(manifest, runtime_cache_root=cache_root)
        self.snapshot_path = snapshot
        return snapshot

    def resolve_asset(
        self,
        asset: Mapping[str, Any],
        cache_root: str | Path,
        *,
        policy: AssetPolicy,
        internet_enabled: bool,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Acquire or validate one exact Hugging Face snapshot."""

        requirement = AssetRequirement(
            asset_id=str(asset["asset_id"]),
            model_or_extractor_id=self.extractor_id,
            revision=str(asset["revision"]),
            source=str(asset["source"]),
            license=str(asset["license"]),
            authentication_required=asset.get("authentication_required", False),
            expected_files=tuple(str(value) for value in asset["expected_files"]),
        )
        root = Path(cache_root)
        root.mkdir(parents=True, exist_ok=True)
        if policy is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD:
            if not internet_enabled:
                raise RuntimeError("online extractor preflight requires model-asset network")
            from huggingface_hub import snapshot_download

            snapshot_download(
                repo_id=requirement.source,
                revision=requirement.revision,
                local_dir=root,
                local_files_only=False,
                token=token,
            )
        elif internet_enabled:
            raise RuntimeError("offline extractor validation requires model-asset network disabled")
        manifest = inventory_cache(requirement, root, policy)
        manifest.update(
            {
                "extractor_id": self.extractor_id,
                "source_repo": requirement.source,
                "layout_type": "direct_local_snapshot",
                "loader_type": "from_pretrained_local_snapshot",
                "snapshot_path": str(root.resolve()),
                "asset_root": str(root.resolve()),
            }
        )
        validate_asset_manifest(manifest, cache_root=root)
        return manifest

    def observed_preprocessing(self, package_versions: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def contract_report(
        self,
        package_versions: Mapping[str, str],
        *,
        difference_report: str | Path | None = None,
    ) -> dict[str, Any]:
        requested = self.requested_contract()
        observed_preprocessing = self.observed_preprocessing(package_versions)
        comparison = compare_preprocessing(
            requested["preprocessing"],
            observed_preprocessing,
            difference_report=difference_report,
        )
        observed = {
            "preprocessing": normalize_contract(observed_preprocessing),
            "output_definition": self.output_definition(),
            "claim_allowed": False,
        }
        return {
            "requested_contract": requested,
            "observed_contract": observed,
            "difference_report": comparison["differences"],
            "preflight_status": "MATCH" if not comparison["differences"] else "MISMATCH",
            "claim_allowed": False,
        }

    def load(self, manifest: Mapping[str, Any], cache_root: str | Path, device: str) -> None:
        raise NotImplementedError

    def extract_batch(self, images: list[Any]) -> Any:
        raise NotImplementedError

    def normalize(self, features: Any) -> Any:
        return features

    def unload(self) -> None:
        self.model = None
        self.processor = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:  # pragma: no cover - optional dependency
            pass


class InceptionExtractorAdapter(ExtractorAdapter):
    adapter_id = "torchvision_inception_v3_local_weight_v1"
    WEIGHT_ENUM = "Inception_V3_Weights.IMAGENET1K_V1"

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        torch_module: Any | None = None,
        torchvision_models: Any | None = None,
    ) -> None:
        super().__init__(config)
        self._torch = torch_module
        self._torchvision_models = torchvision_models

    def _dependencies(self) -> tuple[Any, Any]:
        if self._torch is None:
            import torch

            self._torch = torch
        if self._torchvision_models is None:
            import torchvision.models as models  # type: ignore[import-untyped]

            self._torchvision_models = models
        return self._torch, self._torchvision_models

    def output_definition(self) -> dict[str, Any]:
        return ExtractorOutputDefinition(
            extractor_id="inception",
            model_class="torchvision.models.Inception3",
            processor_class="torchvision.transforms._presets.ImageClassification",
            feature_definition="final_global_average_pool_before_fc_2048d",
            pre_normalization_dimension=2048,
            post_normalization_dimension=2048,
            projection_applied=False,
            l2_normalization_applied=False,
            expected_output_dimension=2048,
        ).as_dict()

    def resolve_asset(
        self,
        asset: Mapping[str, Any],
        cache_root: str | Path,
        *,
        policy: AssetPolicy,
        internet_enabled: bool,
        token: str | None = None,
    ) -> dict[str, Any]:
        del token
        torch, models = self._dependencies()
        root = Path(cache_root)
        root.mkdir(parents=True, exist_ok=True)
        weights = models.Inception_V3_Weights.IMAGENET1K_V1
        expected_enum = str(asset.get("weight_enum", self.WEIGHT_ENUM))
        if expected_enum != self.WEIGHT_ENUM:
            raise ValueError("unsupported or ambiguous Inception weight enum")
        package_version = importlib.metadata.version("torchvision")
        expected_version = str(asset.get("torchvision_package_version", package_version))
        if package_version != expected_version:
            raise ValueError(
                f"Torchvision version differs from the frozen Inception asset contract: {package_version} != {expected_version}"
            )
        filename = Path(weights.url).name
        weight_path = root / filename
        download_seconds = 0.0
        if not weight_path.is_file():
            if policy is not AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD or not internet_enabled:
                raise FileNotFoundError("validated local Inception weight file is missing and offline mode forbids download")
            started = time.monotonic()
            torch.hub.download_url_to_file(weights.url, str(weight_path), progress=True)
            download_seconds = time.monotonic() - started
        digest = file_sha256(weight_path)
        prefix = filename.rsplit("-", 1)[-1].split(".", 1)[0]
        if len(prefix) >= 8 and not digest.startswith(prefix):
            raise ValueError("downloaded Inception weight SHA-256 disagrees with the Torchvision filename prefix")
        root = root.resolve()
        manifest = {
            "schema_version": "certgen.model_asset_manifest.v2",
            "asset_id": str(asset["asset_id"]),
            "extractor_id": "inception",
            "model_or_extractor_id": "inception",
            "revision": str(asset["revision"]),
            "source": weights.url,
            "source_repo": "torchvision.models.Inception_V3_Weights",
            "license": str(asset["license"]),
            "authentication_required": False,
            "files": [filename],
            "file_hashes": {filename: digest},
            "total_size": weight_path.stat().st_size,
            "cache_root": str(root),
            "asset_root": str(root),
            "snapshot_path": str(root),
            "layout_type": "torchvision_local_weight_file",
            "loader_type": "torchvision_local_state_dict",
            "weight_enum": self.WEIGHT_ENUM,
            "torchvision_package_version": package_version,
            "weight_file": filename,
            "expected_feature_dimension": 2048,
            "preprocessing": normalize_contract(observe_inception_contract(package_versions={"torchvision": package_version})),
            "download_seconds": download_seconds,
            "policy": policy.value,
            "validated_at": "runtime_generated",
            "validation_status": "VALIDATED",
            "preflight_status": "ASSET_VALIDATED",
            "local_files_only": policy is AssetPolicy.OFFLINE_PACKAGED_CACHE,
            "evidence_class": "non_evidence_preflight",
            "claim_allowed": False,
        }
        validate_asset_manifest(manifest, cache_root=root)
        return manifest

    def validate_asset(self, manifest: Mapping[str, Any], cache_root: str | Path) -> Path:
        snapshot = super().validate_asset(manifest, cache_root)
        if manifest.get("weight_enum") != self.WEIGHT_ENUM:
            raise ValueError("Inception manifest weight enum mismatch")
        if manifest.get("loader_type") != "torchvision_local_state_dict":
            raise ValueError("Inception must load an explicit local state_dict")
        return snapshot

    def load(self, manifest: Mapping[str, Any], cache_root: str | Path, device: str) -> None:
        snapshot = self.validate_asset(manifest, cache_root)
        torch, models = self._dependencies()
        weight_file = snapshot / str(manifest["weight_file"])
        if file_sha256(weight_file) != manifest["file_hashes"][manifest["weight_file"]]:
            raise ValueError("Inception local weight file changed after preflight")
        weights = models.Inception_V3_Weights.IMAGENET1K_V1
        model = models.inception_v3(weights=None, aux_logits=True)
        state = torch.load(str(weight_file), map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.fc = torch.nn.Identity()
        self.model = model.eval().to(device)
        self.processor = weights.transforms()
        self.device = device

    def observed_preprocessing(self, package_versions: Mapping[str, str]) -> dict[str, Any]:
        return normalize_contract(observe_inception_contract(package_versions=package_versions))

    def extract_batch(self, images: list[Any]) -> Any:
        if self.model is None or self.processor is None or self.device is None:
            raise RuntimeError("Inception adapter is not loaded")
        torch, _ = self._dependencies()
        tensor = torch.stack([self.processor(image) for image in images]).to(self.device)
        return self.model(tensor)


class ClipImageExtractorAdapter(ExtractorAdapter):
    adapter_id = "transformers_clip_projected_image_embedding_v1"

    def __init__(self, config: Mapping[str, Any], *, transformers_module: Any | None = None) -> None:
        super().__init__(config)
        self._transformers = transformers_module

    def _dependency(self) -> Any:
        if self._transformers is None:
            import transformers

            self._transformers = transformers
        return self._transformers

    def output_definition(self) -> dict[str, Any]:
        return ExtractorOutputDefinition(
            extractor_id="clip",
            model_class="transformers.CLIPModel",
            processor_class="transformers.CLIPProcessor",
            feature_definition="projected_image_embedding_from_CLIPModel.get_image_features",
            pre_normalization_dimension=768,
            post_normalization_dimension=768,
            projection_applied=True,
            l2_normalization_applied=True,
            expected_output_dimension=768,
        ).as_dict()

    def load(self, manifest: Mapping[str, Any], cache_root: str | Path, device: str) -> None:
        snapshot = self.validate_asset(manifest, cache_root)
        if manifest.get("loader_type") != "from_pretrained_local_snapshot":
            raise ValueError("CLIP feature extraction requires a direct validated local snapshot")
        transformers = self._dependency()
        self.processor = transformers.CLIPProcessor.from_pretrained(str(snapshot), local_files_only=True)
        self.model = transformers.CLIPModel.from_pretrained(str(snapshot), local_files_only=True).eval().to(device)
        self.device = device

    def observed_preprocessing(self, package_versions: Mapping[str, str]) -> dict[str, Any]:
        if self.processor is None:
            raise RuntimeError("CLIP processor must be loaded before observing preprocessing")
        return normalize_contract(
            observe_transformers_processor(
                extractor_id="clip",
                model_identifier=str(self.config["model_identifier"]),
                revision=str(self.config["revision"]),
                processor=self.processor,
                output_dimension=768,
                package_versions=package_versions,
                feature_normalization="l2",
            )
        )

    def extract_batch(self, images: list[Any]) -> Any:
        if self.model is None or self.processor is None or self.device is None:
            raise RuntimeError("CLIP adapter is not loaded")
        inputs = self.processor(images=images, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)
        features = self.model.get_image_features(pixel_values=pixel_values)
        if hasattr(features, "pooler_output"):  # transformers return_dict compatibility
            features = features.pooler_output
        return self.normalize(features)

    def normalize(self, features: Any) -> Any:
        try:
            import torch

            return torch.nn.functional.normalize(features, dim=-1)
        except ImportError as exc:  # pragma: no cover - optional runtime dependency
            raise RuntimeError("CLIP normalization requires torch") from exc


class DinoOptionalExtractorAdapter(ExtractorAdapter):
    adapter_id = "transformers_dinov2_cls_hidden_state_optional_v1"

    def __init__(self, config: Mapping[str, Any], *, transformers_module: Any | None = None) -> None:
        super().__init__(config)
        self._transformers = transformers_module

    def _dependency(self) -> Any:
        if self._transformers is None:
            import transformers

            self._transformers = transformers
        return self._transformers

    def output_definition(self) -> dict[str, Any]:
        dimension = int(self.config["expected_dimension"])
        return ExtractorOutputDefinition(
            extractor_id="dinov2",
            model_class="transformers.AutoModel resolved to pinned DINOv2 class",
            processor_class="transformers.AutoImageProcessor resolved from pinned snapshot",
            feature_definition="CLS_hidden_state_last_layer",
            pre_normalization_dimension=dimension,
            post_normalization_dimension=dimension,
            projection_applied=False,
            l2_normalization_applied=True,
            expected_output_dimension=dimension,
        ).as_dict()

    def load(self, manifest: Mapping[str, Any], cache_root: str | Path, device: str) -> None:
        snapshot = self.validate_asset(manifest, cache_root)
        transformers = self._dependency()
        self.processor = transformers.AutoImageProcessor.from_pretrained(str(snapshot), local_files_only=True)
        self.model = transformers.AutoModel.from_pretrained(str(snapshot), local_files_only=True).eval().to(device)
        self.device = device

    def observed_preprocessing(self, package_versions: Mapping[str, str]) -> dict[str, Any]:
        if self.processor is None:
            raise RuntimeError("DINOv2 processor must be loaded before observing preprocessing")
        return normalize_contract(
            observe_transformers_processor(
                extractor_id="dinov2",
                model_identifier=str(self.config["model_identifier"]),
                revision=str(self.config["revision"]),
                processor=self.processor,
                output_dimension=int(self.config["expected_dimension"]),
                package_versions=package_versions,
                feature_normalization="l2",
            )
        )

    def extract_batch(self, images: list[Any]) -> Any:
        if self.model is None or self.processor is None or self.device is None:
            raise RuntimeError("DINOv2 adapter is not loaded")
        inputs = self.processor(images=images, return_tensors="pt")
        output = self.model(pixel_values=inputs["pixel_values"].to(self.device))
        return self.normalize(output.last_hidden_state[:, 0])

    def normalize(self, features: Any) -> Any:
        import torch

        return torch.nn.functional.normalize(features, dim=-1)


def adapter_for_extractor(config: Mapping[str, Any]) -> ExtractorAdapter:
    extractor_id = str(config.get("feature_space_id", ""))
    if extractor_id == "inception":
        return InceptionExtractorAdapter(config)
    if extractor_id == "clip":
        return ClipImageExtractorAdapter(config)
    if extractor_id == "dinov2":
        return DinoOptionalExtractorAdapter(config)
    raise ValueError(f"no dedicated extractor adapter is registered for {extractor_id!r}")


def package_versions_for(extractor_id: str, torch_version: str) -> dict[str, str]:
    values = {"torch": torch_version}
    if extractor_id == "inception":
        values["torchvision"] = importlib.metadata.version("torchvision")
    else:
        values["transformers"] = importlib.metadata.version("transformers")
    return values


def resolve_extractor_asset_from_environment(
    adapter: ExtractorAdapter,
    asset: Mapping[str, Any],
    cache_root: str | Path,
    *,
    policy: AssetPolicy,
    internet_enabled: bool,
) -> dict[str, Any]:
    return adapter.resolve_asset(
        asset,
        cache_root,
        policy=policy,
        internet_enabled=internet_enabled,
        token=os.environ.get("HF_TOKEN"),
    )
