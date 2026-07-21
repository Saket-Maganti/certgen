"""Build CIFAR-10 reference sample manifests without downloading data.

The command supports two explicit local layouts:

* already-materialized image trees under ``<root>/<split>/...``;
* the official ``cifar-10-batches-py`` Python-batch archive after the user has
  downloaded/extracted it. In that case images are exported as PPM files under
  ``<root>/certgen_materialized_images``.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import write_json


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ppm", ".bmp"}
CLASS_NAMES = [
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
]
MAX_CIFAR_PICKLE_BYTES = 64 * 1024**2


class _RestrictedCifarUnpickler(pickle.Unpickler):
    """Unpickler limited to the NumPy types used by official CIFAR batches."""

    _ALLOWED_GLOBALS = {
        ("numpy", "ndarray"),
        ("numpy", "dtype"),
        ("numpy.core.multiarray", "_reconstruct"),
        ("numpy._core.multiarray", "_reconstruct"),
        ("numpy.core.multiarray", "scalar"),
        ("numpy._core.multiarray", "scalar"),
    }

    def find_class(self, module: str, name: str) -> Any:
        if (module, name) not in self._ALLOWED_GLOBALS:
            raise pickle.UnpicklingError(f"forbidden CIFAR pickle global: {module}.{name}")
        return super().find_class(module, name)


def _read_ppm_header(path: Path) -> tuple[int, int, int] | None:
    with path.open("rb") as handle:
        magic = handle.readline().strip()
        if magic not in {b"P6", b"P3"}:
            return None
        tokens: list[bytes] = []
        while len(tokens) < 3:
            line = handle.readline()
            if not line:
                break
            line = line.split(b"#", 1)[0]
            tokens.extend(line.split())
        if len(tokens) < 3:
            return None
        return int(tokens[0]), int(tokens[1]), 3


def _read_png_header(path: Path) -> tuple[int, int, int] | None:
    data = path.read_bytes()[:32]
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 26:
        return None
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    color_type = data[25]
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type, 3)
    return width, height, channels


def _image_info(path: Path) -> tuple[int, int, int]:
    if path.suffix.lower() == ".ppm":
        info = _read_ppm_header(path)
        if info:
            return info
    if path.suffix.lower() == ".png":
        info = _read_png_header(path)
        if info:
            return info
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - exercised only without image headers.
        raise ValueError(f"cannot determine image dimensions for {path}; install Pillow or use PNG/PPM") from exc
    with Image.open(path) as image:
        channels = len(image.getbands())
        width, height = image.size
    return int(width), int(height), int(channels)


def _candidate_image_roots(root: Path, split: str) -> list[Path]:
    if split == "all":
        return [root / "train", root / "test"] if (root / "train").exists() or (root / "test").exists() else [root]
    return [root / split] if (root / split).exists() else [root]


def _infer_split(path: Path, root: Path, requested_split: str) -> str:
    if requested_split != "all":
        return requested_split
    parts = set(path.relative_to(root).parts)
    if "train" in parts:
        return "train"
    if "test" in parts:
        return "test"
    return "unknown"


def _infer_class_label(path: Path, split_value: str) -> str | None:
    parent = path.parent.name
    if parent in {"train", "test", "all", "."}:
        return None
    if parent == split_value:
        return None
    return parent


def _entry_for_image(
    *,
    path: Path,
    root: Path,
    split: str,
    source_url: str,
    license_status: str,
    index: int,
) -> dict[str, Any]:
    width, height, channels = _image_info(path)
    rel = path.relative_to(root) if path.is_relative_to(root) else path
    split_value = _infer_split(path, root, split)
    class_label = _infer_class_label(path, split_value)
    sample_id = f"cifar10_{split_value}_{index:05d}_{stable_hash_json(str(rel))[:8]}"
    return {
        "sample_id": sample_id,
        "role": "reference",
        "path": str(path),
        "relative_path": str(rel),
        "split": split_value,
        "class_label": class_label,
        "width": width,
        "height": height,
        "channels": channels,
        "source_id": "cifar10_reference",
        "source_url": source_url,
        "license_status": license_status,
        "sha256": file_sha256(path),
        "hash": file_sha256(path),
        "evidence_status": "r1a_sample_package_non_evidence",
        "claim_allowed": False,
    }


def _find_images(root: Path, split: str) -> list[Path]:
    images: list[Path] = []
    for candidate_root in _candidate_image_roots(root, split):
        if candidate_root.exists():
            images.extend(path for path in candidate_root.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file())
    return sorted(set(images), key=lambda item: str(item))


def _batch_root(root: Path) -> Path | None:
    direct = root / "cifar-10-batches-py"
    if direct.exists():
        return direct
    if (root / "test_batch").exists() or (root / "data_batch_1").exists():
        return root
    return None


def _load_pickle(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size <= 0 or size > MAX_CIFAR_PICKLE_BYTES:
        raise ValueError(f"CIFAR pickle size outside allowed range: {path} ({size} bytes)")
    with path.open("rb") as handle:
        loaded = _RestrictedCifarUnpickler(handle, encoding="latin1").load()
    if not isinstance(loaded, dict):
        raise ValueError(f"CIFAR pickle must contain a dictionary: {path}")
    return {str(key): value for key, value in loaded.items()}


def _write_ppm(array: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width, channels = array.shape
    if channels != 3:
        raise ValueError(f"expected RGB array, got shape {array.shape}")
    payload = f"P6\n{width} {height}\n255\n".encode("ascii") + array.astype(np.uint8, copy=False).tobytes()
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"refusing to overwrite mismatched materialized image: {path}")
        return
    path.write_bytes(payload)


def _export_cifar_batches(root: Path, split: str) -> tuple[list[Path], dict[str, int]]:
    batch_dir = _batch_root(root)
    if not batch_dir:
        return [], {}
    meta_path = batch_dir / "batches.meta"
    label_names = CLASS_NAMES
    if meta_path.exists():
        meta = _load_pickle(meta_path)
        label_names = [str(item) for item in meta.get("label_names", CLASS_NAMES)]
    wanted = []
    if split in {"train", "all"}:
        wanted.extend((f"data_batch_{idx}", "train") for idx in range(1, 6))
    if split in {"test", "all"}:
        wanted.append(("test_batch", "test"))

    exported: list[Path] = []
    counts = {"train": 0, "test": 0}
    out_root = root / "certgen_materialized_images"
    for file_name, split_name in wanted:
        batch_path = batch_dir / file_name
        if not batch_path.exists():
            continue
        batch = _load_pickle(batch_path)
        if "data" not in batch:
            raise ValueError(f"official CIFAR batch is missing data: {batch_path}")
        raw_data = np.asarray(batch["data"])
        if raw_data.shape != (10_000, 3 * 32 * 32) or raw_data.dtype != np.uint8:
            raise ValueError(
                f"official CIFAR batch data must be uint8[10000,3072], got {raw_data.dtype}{raw_data.shape}: {batch_path}"
            )
        data = raw_data.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)
        labels = [int(item) for item in batch.get("labels", batch.get("fine_labels", []))]
        if len(labels) != 10_000 or any(label < 0 or label >= len(label_names) for label in labels):
            raise ValueError(f"official CIFAR batch labels invalid: {batch_path}")
        for item_idx, image in enumerate(data):
            label = labels[item_idx] if item_idx < len(labels) else -1
            class_name = label_names[label] if 0 <= label < len(label_names) else "unknown"
            global_idx = counts[split_name]
            out_path = out_root / split_name / class_name / f"cifar10_{split_name}_{global_idx:05d}.ppm"
            _write_ppm(image, out_path)
            exported.append(out_path)
            counts[split_name] += 1
    return exported, counts


def build_reference_manifest(
    *,
    cifar_root: str | Path,
    split: str,
    out_manifest: str | Path,
    out_summary: str | Path,
    license_status: str,
    source_url: str,
    claim_allowed: bool = False,
) -> dict[str, Any]:
    if claim_allowed:
        raise ValueError("R1A reference manifests must keep claim_allowed=false")
    root = Path(cifar_root)
    if split not in {"train", "test", "all"}:
        raise ValueError("split must be train, test, or all")
    if not root.exists():
        raise FileNotFoundError(f"CIFAR root does not exist: {root}")

    images = _find_images(root, split)
    source_layout = "materialized_image_tree"
    batch_counts: dict[str, int] = {}
    if not images:
        images, batch_counts = _export_cifar_batches(root, split)
        source_layout = "official_python_batches_exported_to_ppm"
    if not images:
        raise FileNotFoundError(f"no CIFAR-10 images or official Python batches found under {root}")

    rows = [
        _entry_for_image(path=path, root=root, split=split, source_url=source_url, license_status=license_status, index=index)
        for index, path in enumerate(images)
    ]
    counts_by_split: dict[str, int] = {}
    for row in rows:
        counts_by_split[row["split"]] = counts_by_split.get(row["split"], 0) + 1

    out_manifest = Path(out_manifest)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    with out_manifest.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "dataset": "cifar10",
        "source_id": "cifar10_reference",
        "source_url": source_url,
        "split_requested": split,
        "source_layout": source_layout,
        "rows": len(rows),
        "counts_by_split": counts_by_split,
        "batch_counts": batch_counts,
        "license_status": license_status,
        "validation_status": "passed",
        "evidence_status": "r1a_sample_package_non_evidence",
        "claim_allowed": False,
        "out_manifest": str(out_manifest),
    }
    write_json(summary, out_summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a CIFAR-10 reference sample manifest from local files.")
    parser.add_argument("--cifar-root", required=True)
    parser.add_argument("--split", choices=["train", "test", "all"], required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--out-summary", required=True)
    parser.add_argument("--license-status", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--claim-allowed", default="false", choices=["false"])
    args = parser.parse_args(argv)
    try:
        summary = build_reference_manifest(
            cifar_root=args.cifar_root,
            split=args.split,
            out_manifest=args.out_manifest,
            out_summary=args.out_summary,
            license_status=args.license_status,
            source_url=args.source_url,
            claim_allowed=False,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"wrote {summary['rows']} CIFAR-10 reference rows -> {summary['out_manifest']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
