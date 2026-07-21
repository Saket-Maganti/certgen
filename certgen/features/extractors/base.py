"""Feature extraction adapters.

Real extraction is implemented here through small, overridable hooks. Heavy
dependencies (``torch``/``torchvision``/``transformers``/``PIL``) are imported
lazily *inside* the hooks, so importing this module -- and running the
CPU-only statistical test suite -- never requires the vision stack. Each
extractor writes a feature ``.npz`` plus a schema-aligned sidecar that records
the model id, preprocessing lock, sample ids, and content hash. Output is always
``claim_allowed=False`` and ``real_features_unvalidated``; promoting it to
evidence is a separate validation + reproduction gate.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


class OptionalDependencyMissing(RuntimeError):
    pass


def read_input_manifest(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


@dataclass
class FeatureExtractor:
    name: str
    feature_dim: int
    heavy_dependencies: list[str]

    def _resolved_model_metadata(self) -> dict[str, Any]:
        return {
            "model_id": getattr(self, "resolved_model_id", None),
            "model_revision": getattr(self, "resolved_model_revision", None),
            "weights_id": getattr(self, "resolved_weights_id", None),
            "weights_url": getattr(self, "resolved_weights_url", None),
            "license_status": getattr(self, "resolved_license_status", "unknown"),
        }

    def is_available(self) -> bool:
        return all(importlib.util.find_spec(dep) is not None for dep in self.heavy_dependencies)

    def dry_run_plan(self, input_manifest: str | Path, out_dir: str | Path, batch_size: int, device: str) -> dict[str, Any]:
        rows = read_input_manifest(input_manifest)
        missing = [row.get("path") for row in rows if row.get("path") and not Path(row["path"]).exists()]
        batches = (len(rows) + max(1, batch_size) - 1) // max(1, batch_size)
        out_dir = Path(out_dir)
        return {
            "extractor": self.name,
            "feature_dim": self.feature_dim,
            "item_count": len(rows),
            "missing_local_files_count": len(missing),
            "missing_local_files": missing,
            "estimated_batches": batches,
            "device_request": device,
            "extractor_available": self.is_available(),
            "heavy_dependencies": self.heavy_dependencies,
            "output_feature_path": str(out_dir / f"{self.name}_features.npz"),
            "output_sidecar_path": str(out_dir / f"{self.name}_features.json"),
            "evidence_status": "dry_run_only",
            "claim_allowed": False,
        }

    # ------------------------------------------------------------------
    # Overridable model hooks (lazy heavy imports live here).
    # ------------------------------------------------------------------
    def _resolve_device(self, device: str) -> str:
        if device and device != "auto":
            return device
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _load_backbone(self, device: str, model_id: str | None, preprocessing: dict[str, Any] | None) -> tuple[Any, Any]:
        raise NotImplementedError(f"{self.name} does not implement a real backbone loader")

    def _forward(self, model: Any, batch: Any) -> np.ndarray:
        raise NotImplementedError(f"{self.name} does not implement a forward embedding")

    def _load_image(self, path: str) -> Any:
        from PIL import Image

        return Image.open(path).convert("RGB")

    def _embed_paths(self, model: Any, transform: Any, paths: list[str], device: str, batch_size: int) -> np.ndarray:
        import torch

        chunks: list[np.ndarray] = []
        for start in range(0, len(paths), max(1, batch_size)):
            batch_paths = paths[start : start + max(1, batch_size)]
            tensors = [transform(self._load_image(path)) for path in batch_paths]
            batch = torch.stack(tensors).to(device)
            with torch.no_grad():
                chunks.append(np.asarray(self._forward(model, batch), dtype=np.float32))
        return np.concatenate(chunks, axis=0) if chunks else np.empty((0, self.feature_dim), dtype=np.float32)

    # ------------------------------------------------------------------
    # Orchestration.
    # ------------------------------------------------------------------
    def extract(
        self,
        input_manifest: str | Path,
        out_dir: str | Path,
        batch_size: int,
        device: str,
        max_items: int | None = None,
        *,
        model_id: str | None = None,
        preprocessing: dict[str, Any] | None = None,
        evidence_status: str = "real_features_unvalidated",
    ) -> dict[str, Any]:
        if not self.is_available():
            raise OptionalDependencyMissing(f"{self.name} requires optional dependencies: {', '.join(self.heavy_dependencies)}")

        rows = read_input_manifest(input_manifest)
        if max_items is not None:
            rows = rows[: int(max_items)]
        if not rows:
            raise ValueError("input manifest is empty; nothing to extract")
        paths = [str(row["path"]) for row in rows]
        sample_ids = [str(row.get("sample_id", index)) for index, row in enumerate(rows)]
        missing = [path for path in paths if not Path(path).exists()]
        if missing:
            raise ValueError(f"{len(missing)} manifest paths do not exist locally (first: {missing[0]})")

        resolved_device = self._resolve_device(device)
        model, transform = self._load_backbone(resolved_device, model_id, preprocessing)
        model_metadata = self._resolved_model_metadata()
        if not model_metadata.get("model_id") or not model_metadata.get("model_revision"):
            raise ValueError(f"{self.name} did not declare a resolved model id and immutable revision/weights id")
        features = np.asarray(self._embed_paths(model, transform, paths, resolved_device, batch_size), dtype=np.float32)
        if features.ndim != 2 or features.shape[0] != len(paths):
            raise ValueError(f"extractor produced features of shape {features.shape} for {len(paths)} inputs")
        if features.shape[1] != self.feature_dim:
            raise ValueError(f"{self.name} expected feature_dim {self.feature_dim}, got {features.shape[1]}")

        out_dir = Path(out_dir)
        feature_path = out_dir / f"{self.name}_features.npz"
        sidecar_path = out_dir / f"{self.name}_features.json"
        out_dir.mkdir(parents=True, exist_ok=True)

        from certgen.core.io import save_feature_npz, write_json

        array_info = save_feature_npz(features, feature_path)
        sidecar = {
            "extractor": self.name,
            "model_id": model_metadata["model_id"],
            "requested_model_id": model_id,
            "model_revision": model_metadata["model_revision"],
            "weights_id": model_metadata["weights_id"],
            "weights_url": model_metadata["weights_url"],
            "feature_type": self.name,
            "feature_dim": int(features.shape[1]),
            "num_items": int(features.shape[0]),
            "sample_ids": sample_ids,
            "preprocessing": preprocessing or {},
            "source": model_metadata,
            "dependency_versions": {
                dependency: importlib.metadata.version(dependency)
                for dependency in self.heavy_dependencies
                if importlib.util.find_spec(dependency) is not None
            },
            "device": resolved_device,
            "feature_path": str(feature_path),
            "shape": array_info["shape"],
            "dtype": array_info["dtype"],
            "hash": array_info["hash"],
            "evidence_status": evidence_status,
            "claim_allowed": False,
            "limitations": [
                "NO_REAL_EVIDENCE_UNTIL_VALIDATION",
                "features require cache validation and metric reproduction before certification",
                "exact metric reproduction depends on matching canonical extractor weights and preprocessing lock",
            ],
        }
        write_json(sidecar, sidecar_path)
        return {
            "extractor": self.name,
            "feature_path": str(feature_path),
            "sidecar_path": str(sidecar_path),
            "num_items": int(features.shape[0]),
            "feature_dim": int(features.shape[1]),
            "model_id": model_metadata["model_id"],
            "model_revision": model_metadata["model_revision"],
            "hash": array_info["hash"],
            "evidence_status": evidence_status,
            "claim_allowed": False,
        }
