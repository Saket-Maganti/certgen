"""Detect local CIFAR-10 source layouts without downloading data."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


CLASS_NAMES = {
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
}


@dataclass(frozen=True)
class CifarDetection:
    status: str
    detected_path: str | None
    layout: str
    blocker_code: str | None
    counts: dict[str, int]
    claim_allowed: bool = False
    evidence_status: str = "NO_REAL_EVIDENCE"


def detect_cifar10_root(search_root: str | Path) -> CifarDetection:
    root = Path(search_root).expanduser()
    if not root.exists():
        return CifarDetection(
            "blocked",
            None,
            "missing",
            "BLOCKED_CIFAR_SEARCH_ROOT_MISSING",
            {},
        )
    candidates = [root, *[p for p in root.rglob("*") if p.is_dir()]]
    for candidate in candidates:
        names = {p.name for p in candidate.iterdir()} if candidate.exists() else set()
        if {"data_batch_1", "data_batch_2", "data_batch_3", "data_batch_4", "data_batch_5"}.issubset(
            names
        ):
            return CifarDetection(
                "ready",
                str(candidate),
                "official_cifar_10_batches_py",
                None,
                {"batch_files": 5},
            )
        if (candidate / "cifar-10-batches-py").is_dir():
            batch_dir = candidate / "cifar-10-batches-py"
            return CifarDetection(
                "ready",
                str(batch_dir),
                "official_cifar_10_batches_py",
                None,
                {"batch_files": len(list(batch_dir.glob("data_batch_*")))},
            )
        class_dirs = [p for p in candidate.iterdir() if p.is_dir() and p.name.lower() in CLASS_NAMES]
        if len(class_dirs) >= 2:
            image_count = sum(
                len(list(p.glob("*.png"))) + len(list(p.glob("*.jpg"))) + len(list(p.glob("*.jpeg")))
                for p in class_dirs
            )
            return CifarDetection(
                "ready",
                str(candidate),
                "image_folder_class_tree",
                None,
                {"class_dirs": len(class_dirs), "image_files": image_count},
            )
        if (candidate / "manifest.csv").exists() or (candidate / "manifest.jsonl").exists():
            image_count = (
                len(list(candidate.glob("*.png")))
                + len(list(candidate.glob("*.jpg")))
                + len(list(candidate.glob("*.jpeg")))
            )
            return CifarDetection(
                "ready",
                str(candidate),
                "flat_image_directory_with_manifest",
                None,
                {"image_files": image_count, "manifest_files": 1},
            )
    return CifarDetection(
        "blocked",
        None,
        "unsupported_or_no_cifar10_data_found",
        "BLOCKED_MISSING_REFERENCE_SAMPLES",
        {},
    )


def write_detection_report(detection: CifarDetection, path: str | Path) -> None:
    text = f"""# V7 CIFAR-10 Root Detection Report

Status: `{detection.status}`
Layout: `{detection.layout}`
Detected path: `{detection.detected_path}`
Blocker: `{detection.blocker_code}`
Claim allowed: `{str(detection.claim_allowed).lower()}`
Evidence status: `{detection.evidence_status}`

Next command: `CIFAR_ROOT=<detected_path> bash commands/v7_cpu_execution/01_auto_materialize_cifar_reference.sh`
"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-root", default=".")
    parser.add_argument("--out-json", default="data/results/v7_cifar_root_detection.json")
    parser.add_argument("--out-report", default="docs/V7_CIFAR_REFERENCE_ONRAMP_REPORT.md")
    args = parser.parse_args(argv)
    detection = detect_cifar10_root(args.search_root)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(asdict(detection), indent=2) + "\n", encoding="utf-8")
    write_detection_report(detection, args.out_report)
    print(json.dumps(asdict(detection), indent=2, sort_keys=True))
    return 0 if detection.status == "ready" else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
