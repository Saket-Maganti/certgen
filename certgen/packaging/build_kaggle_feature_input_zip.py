"""Build the Kaggle input ZIP for CIFAR-10 feature extraction."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.packaging.common import add_repo_file, add_text_file, file_info, has_claim_allowed_true, read_jsonl, scan_text_for_private_paths_or_secrets, write_zip_json


README = """# CertGen CIFAR-10 Feature Extraction Input Package

This package is for Kaggle T4x2 Inception/CLIP feature extraction only.

It does not run metric reproduction, certificates, pilot undecided-fraction
reporting, or paper evidence generation.

claim_allowed=false
NO_FAKE_RESULTS
NO_REAL_EVIDENCE until gates pass
not paper evidence
"""


ROLES = ["reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"]
FEATURE_EXTRACTOR_LOCKS = {
    "inception_v3_pool3": "torchvision::Inception_V3_Weights.IMAGENET1K_V1",
    "clip_vit": "openai/clip-vit-large-patch14@32bd64288804d66eefd0ccbe215aa642df71cc41",
}
FEATURE_CODE_FILES = [
    "certgen/__init__.py",
    "certgen/cli/__init__.py",
    "certgen/cli/run_feature_extraction.py",
    "certgen/core/__init__.py",
    "certgen/core/hashing.py",
    "certgen/core/io.py",
    "certgen/features/__init__.py",
    "certgen/features/extract.py",
    "certgen/features/merge_shards.py",
    "certgen/features/split_by_role.py",
    "certgen/features/extractors/__init__.py",
    "certgen/features/extractors/base.py",
    "certgen/features/extractors/clip.py",
    "certgen/features/extractors/dinov2.py",
    "certgen/features/extractors/inception.py",
]


def _sanitized_rows(rows: list[dict[str, Any]], *, image_policy: str, image_prefix: str) -> tuple[list[dict[str, Any]], list[tuple[Path, str]], list[str]]:
    sanitized: list[dict[str, Any]] = []
    files: list[tuple[Path, str]] = []
    errors: list[str] = []
    for row in rows:
        if has_claim_allowed_true(row):
            errors.append(f"{row.get('sample_id', '<unknown>')}: claim_allowed=true")
        row = dict(row)
        role = str(row.get("role") or row.get("source_id") or "unknown")
        sample_id = str(row.get("sample_id") or Path(str(row.get("path") or "sample")).stem)
        local_path = Path(str(row.get("path") or row.get("image_path") or ""))
        if image_policy == "include_images":
            if not local_path.exists():
                errors.append(f"{sample_id}: local image missing: {local_path}")
                row["path"] = f"missing/{sample_id}"
            else:
                arcname = f"{image_prefix}/{role}/{local_path.name}"
                files.append((local_path, arcname))
                row["path"] = arcname
                row["image_path"] = arcname
        else:
            row.pop("absolute_path", None)
            row["path"] = f"KAGGLE_DATASET_MOUNT_REQUIRED/{role}/{sample_id}"
            row["image_path"] = row["path"]
            row["user_provided_local_path_redacted"] = True
        row["claim_allowed"] = False
        row["not_paper_evidence"] = True
        sanitized.append(row)
    return sanitized, files, errors


def build_feature_input_zip(
    *,
    reference_manifest: str | Path,
    generated_manifest: str | Path,
    provenance_ledger: str | Path,
    preprocessing_lock: str | Path,
    out_zip: str | Path,
    manifest_out: str | Path,
    sample_manifest: str | Path | None = None,
    image_policy: str = "manifest_paths",
    expected_reference_count: int = 10000,
    expected_generated_count_per_model: int = 1000,
    dry_run: bool = False,
) -> dict[str, Any]:
    for required in [reference_manifest, generated_manifest, provenance_ledger, preprocessing_lock]:
        if not Path(required).exists():
            raise FileNotFoundError(f"required input missing: {required}")
    reference_rows = read_jsonl(reference_manifest)
    generated_rows = read_jsonl(generated_manifest)
    sample_rows = read_jsonl(sample_manifest) if sample_manifest and Path(sample_manifest).exists() else reference_rows + generated_rows
    sanitized_reference, reference_files, reference_errors = _sanitized_rows(reference_rows, image_policy=image_policy, image_prefix="samples/reference")
    sanitized_generated, generated_files, generated_errors = _sanitized_rows(generated_rows, image_policy=image_policy, image_prefix="samples/generated")
    sanitized_samples, sample_files, sample_errors = _sanitized_rows(sample_rows, image_policy=image_policy, image_prefix="samples/all")
    errors = reference_errors + generated_errors + sample_errors
    manifest = {
        "package_type": "certgen_cifar10_feature_extraction_input",
        "status_code": "DRY_RUN" if dry_run else ("FEATURE_INPUT_ZIP_READY" if not errors else "BLOCKED_FEATURE_INPUT_PACKAGE_INVALID"),
        "passed": (not dry_run) and not errors,
        "out_zip": str(out_zip),
        "reference_count": len(reference_rows),
        "generated_count": len(generated_rows),
        "expected_reference_count": expected_reference_count,
        "expected_generated_count_per_model": expected_generated_count_per_model,
        "roles": ROLES,
        "image_policy": image_policy,
        "split_zip_policy": ["reference.zip", "generated_google_ddpm.zip", "generated_frank_ddpm_ema.zip", "generated_frank_cfm.zip", "configs_and_manifests.zip"],
        "errors": errors,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    if dry_run:
        write_json(manifest, manifest_out)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return manifest
    if errors:
        write_json(manifest, manifest_out)
        return manifest
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        raise FileExistsError(f"refusing to overwrite existing feature input ZIP: {out_zip}")
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        add_text_file(zf, "README.md", README)
        for rows, arcname in [
            (sanitized_reference, "manifests/cifar10_r1_reference.jsonl"),
            (sanitized_generated, "manifests/cifar10_r1_generated_pilot_1000.jsonl"),
            (sanitized_samples, "manifests/cifar10_r1_feature_extraction_samples.jsonl"),
        ]:
            zf.writestr(arcname, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        zf.write(provenance_ledger, "inputs/cifar10_r1_ledger.csv")
        zf.write(preprocessing_lock, f"configs/{Path(preprocessing_lock).name}")
        write_zip_json(
            zf,
            "config/feature_extraction_config.json",
            {
                "extractors": ["inception_v3_pool3", "clip_vit"],
                "extractor_locks": FEATURE_EXTRACTOR_LOCKS,
                "roles": ROLES,
                "expected_counts": {"reference": expected_reference_count, "per_generated_model": expected_generated_count_per_model},
                "claim_allowed": False,
                "not_paper_evidence": True,
            },
        )
        for src, arcname in reference_files + generated_files + sample_files:
            zf.write(src, arcname)
        add_repo_file(zf, "pyproject.toml", "repo/pyproject.toml")
        for source in FEATURE_CODE_FILES:
            add_repo_file(zf, source, f"repo/{source}")
        write_zip_json(zf, "metadata/package_manifest.json", manifest)
    with zipfile.ZipFile(out_zip, "r") as zf:
        issues = scan_text_for_private_paths_or_secrets("\n".join(zf.namelist()))
        if issues:
            raise ValueError(f"unsafe feature input ZIP: {issues}")
        manifest["zip_files"] = sorted(zf.namelist())
    manifest["zip_info"] = file_info(out_zip)
    write_json(manifest, manifest_out)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the CertGen Kaggle feature extraction input ZIP.")
    parser.add_argument("--reference-manifest", default="registry/manifests/cifar10_r1_reference.jsonl")
    parser.add_argument("--generated-manifest", default="registry/manifests/cifar10_r1_generated_pilot_1000.jsonl")
    parser.add_argument("--sample-manifest", default="registry/manifests/cifar10_r1_feature_extraction_samples.jsonl")
    parser.add_argument("--provenance-ledger", default="registry/provenance/cifar10_r1_ledger.csv")
    parser.add_argument("--preprocessing-lock", default="configs/preprocessing_locks/cifar10_inception_bilinear_299.json")
    parser.add_argument("--out-zip", default="data/kaggle_inputs/certgen_cifar10_feature_extraction_1k_input.zip")
    parser.add_argument("--manifest-out", default="data/results/v6_feature_input_zip_manifest.json")
    parser.add_argument("--image-policy", default="manifest_paths", choices=["manifest_paths", "include_images"])
    parser.add_argument("--expected-reference-count", type=int, default=10000)
    parser.add_argument("--expected-generated-count-per-model", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = build_feature_input_zip(
            reference_manifest=args.reference_manifest,
            generated_manifest=args.generated_manifest,
            provenance_ledger=args.provenance_ledger,
            preprocessing_lock=args.preprocessing_lock,
            out_zip=args.out_zip,
            manifest_out=args.manifest_out,
            sample_manifest=args.sample_manifest,
            image_policy=args.image_policy,
            expected_reference_count=args.expected_reference_count,
            expected_generated_count_per_model=args.expected_generated_count_per_model,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Feature input ZIP status: {manifest['status_code']}")
    return 0 if manifest["passed"] or args.dry_run else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
