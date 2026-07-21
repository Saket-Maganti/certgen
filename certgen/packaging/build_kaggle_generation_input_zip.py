"""Build the Kaggle input ZIP for CIFAR-10 sample generation."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
from certgen.packaging.common import (
    add_repo_file,
    add_text_file,
    default_checkpoints,
    file_info,
    scan_text_for_private_paths_or_secrets,
    seed_shard_plan,
    write_zip_json,
)


README = """# CertGen CIFAR-10 Generation Input Package

This package is for Kaggle T4x2 sample generation only.

It creates sample-package artifacts. It does not run feature extraction,
metric reproduction, certificates, pilot undecided-fraction reporting, or
paper evidence generation.

claim_allowed=false
NO_FAKE_RESULTS
NO_REAL_EVIDENCE until gates pass
not paper evidence
"""


MINIMAL_CODE_FILES = [
    "pyproject.toml",
    "certgen/__init__.py",
    "certgen/core/hashing.py",
    "certgen/core/io.py",
    "certgen/generation/__init__.py",
    "certgen/generation/generate_cifar10_diffusers.py",
    "certgen/generation/merge_sample_manifests.py",
    "certgen/generation/validate_cifar10_generated_pilot.py",
]


def _load_checkpoints(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return default_checkpoints()
    loaded = read_json(path)
    checkpoints = loaded.get("checkpoints", loaded)
    if not isinstance(checkpoints, list):
        raise ValueError("checkpoint list must be a JSON list or an object with checkpoints")
    return [dict(item) for item in checkpoints]


def _generation_config(sample_count_per_model: int, config_path: str | Path | None) -> dict[str, Any]:
    config = read_json(config_path) if config_path else {}
    config.update(
        {
            "dataset": "cifar10",
            "sample_count_per_model": int(sample_count_per_model),
            "image_size": 32,
            "channels": 3,
            "generation_stage": "sample_package_only",
            "claim_allowed": False,
            "no_fake_results": True,
            "not_paper_evidence": True,
        }
    )
    return config


def build_generation_input_zip(
    *,
    provenance_ledger: str | Path,
    out_zip: str | Path,
    manifest_out: str | Path,
    checkpoint_list: str | Path | None = None,
    generation_config: str | Path | None = None,
    requirements_file: str | Path | None = None,
    sample_count_per_model: int = 1000,
    include_source_mode: str = "minimal",
    dry_run: bool = False,
) -> dict[str, Any]:
    checkpoints = _load_checkpoints(checkpoint_list)
    config = _generation_config(sample_count_per_model, generation_config)
    shard_plan = seed_shard_plan(sample_count_per_model)
    provenance_path = Path(provenance_ledger)
    if not provenance_path.exists():
        raise FileNotFoundError(f"provenance ledger missing: {provenance_path}")
    manifest = {
        "package_type": "certgen_cifar10_generation_input",
        "status_code": "DRY_RUN" if dry_run else "GENERATION_INPUT_ZIP_READY",
        "passed": not dry_run,
        "out_zip": str(out_zip),
        "sample_count_per_model": int(sample_count_per_model),
        "checkpoints": checkpoints,
        "seed_shard_plan": shard_plan,
        "include_source_mode": include_source_mode,
        "provenance_ledger": str(provenance_path),
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    if dry_run:
        write_json(manifest, manifest_out)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return manifest

    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        raise FileExistsError(f"refusing to overwrite existing generation input ZIP: {out_zip}")
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        add_text_file(zf, "README.md", README)
        write_zip_json(zf, "config/generation_config.json", config)
        write_zip_json(zf, "config/checkpoints.json", {"checkpoints": checkpoints, "claim_allowed": False})
        write_zip_json(zf, "config/seed_shard_plan.json", {"shards": shard_plan, "claim_allowed": False})
        write_zip_json(
            zf,
            "schemas/generated_manifest_schema.json",
            {
                "required": ["sample_id", "checkpoint_id", "seed", "image_path", "image_hash", "width", "height", "channels", "generation_status", "claim_allowed"],
                "claim_allowed": False,
            },
        )
        zf.write(provenance_path, "inputs/cifar10_r1_ledger.csv")
        if requirements_file:
            add_repo_file(zf, requirements_file, "requirements.txt")
        elif Path("requirements.txt").exists():
            add_repo_file(zf, "requirements.txt", "requirements.txt")
        if include_source_mode == "minimal":
            for src in MINIMAL_CODE_FILES:
                add_repo_file(zf, src, f"repo/{src}")
        write_zip_json(zf, "metadata/package_manifest.json", manifest)

    with zipfile.ZipFile(out_zip, "r") as zf:
        text = "\n".join(zf.namelist())
        issues = scan_text_for_private_paths_or_secrets(text)
        if issues:
            raise ValueError(f"unsafe zip names: {issues}")
        manifest["zip_files"] = sorted(zf.namelist())
    manifest["zip_info"] = file_info(out_zip)
    manifest["passed"] = True
    write_json(manifest, manifest_out)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the CertGen Kaggle generation input ZIP.")
    parser.add_argument("--provenance-ledger", default="registry/provenance/cifar10_r1_ledger.csv")
    parser.add_argument("--checkpoint-list")
    parser.add_argument("--generation-config")
    parser.add_argument("--out-zip", default="data/kaggle_inputs/certgen_cifar10_generation_1k_input.zip")
    parser.add_argument("--manifest-out", default="data/results/v6_generation_input_zip_manifest.json")
    parser.add_argument("--include-source-mode", default="minimal", choices=["minimal", "none"])
    parser.add_argument("--requirements-file")
    parser.add_argument("--sample-count-per-model", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = build_generation_input_zip(
            provenance_ledger=args.provenance_ledger,
            out_zip=args.out_zip,
            manifest_out=args.manifest_out,
            checkpoint_list=args.checkpoint_list,
            generation_config=args.generation_config,
            requirements_file=args.requirements_file,
            sample_count_per_model=args.sample_count_per_model,
            include_source_mode=args.include_source_mode,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Generation input ZIP status: {manifest['status_code']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
