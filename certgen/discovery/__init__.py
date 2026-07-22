"""Universal Kaggle/local discovery selected by internal identity and hashes."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Iterable

from certgen.discovery.classify import classify_package
from certgen.discovery.models import (
    CandidateForm,
    DiscoveryLimits,
    DiscoveryResult,
    ExpectedPackageIdentity,
    PackageCandidate,
    PackageRequirement,
    PackageType,
    SelectionStatus,
)
from certgen.discovery.roots import configured_roots
from certgen.discovery.scan import scan_package_candidates
from certgen.discovery.select import mismatch_reasons
from certgen.discovery.specialized import (
    discover_asset_mount,
    discover_dataset_root,
    discover_reference,
    discover_wheelhouse,
    validate_resolved_asset,
    write_asset_resolution_report,
)


def discover_packages(
    search_roots: Iterable[str | Path],
    *,
    requirement: PackageRequirement | None = None,
    limits: DiscoveryLimits | None = None,
) -> DiscoveryResult:
    selected_requirement = requirement or PackageRequirement()
    selected_limits = limits or DiscoveryLimits()
    roots = tuple(Path(root).resolve(strict=False) for root in search_roots)
    paths, report = scan_package_candidates(roots, limits=selected_limits)
    candidates = tuple(classify_package(path, limits=selected_limits) for path in paths)
    reasons = {str(row.path): mismatch_reasons(row, selected_requirement) for row in candidates}
    matches = tuple(row for row in candidates if not reasons[str(row.path)])
    distinct_hashes = {row.package_sha256 for row in matches}
    if len(matches) == 1:
        status = SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE
        selected = matches[0]
    elif matches and len(distinct_hashes) == 1:
        status = SelectionStatus.DUPLICATE_IDENTICAL_COPY_DEDUPED
        selected = sorted(matches, key=lambda row: str(row.path).casefold())[0]
    elif not matches:
        status = SelectionStatus.NO_MATCHING_PACKAGE
        selected = None
    else:
        status = SelectionStatus.AMBIGUOUS_DIFFERENT_CONTENT
        selected = None
    return DiscoveryResult(
        status=status,
        requirement=selected_requirement,
        candidates=candidates,
        matching_candidates=matches,
        selected=selected,
        scan=report,
        reasons=reasons,
    )


def materialize_selected_package(
    candidate: PackageCandidate,
    *,
    destination: str | Path,
    limits: DiscoveryLimits | None = None,
) -> Path:
    if not candidate.valid:
        raise ValueError("cannot materialize an invalid package")
    if candidate.form is CandidateForm.EXTRACTED_DIRECTORY:
        verified = classify_package(candidate.path, limits=limits)
        if not verified.valid or verified.identity.scientific_identity_hash != candidate.identity.scientific_identity_hash:
            raise ValueError("extracted package changed after selection")
        return candidate.path
    selected_limits = limits or DiscoveryLimits()
    output = Path(destination)
    marker = output / ".source_sha256"
    if output.is_dir():
        if marker.is_file() and marker.read_text(encoding="utf-8").strip() == candidate.package_sha256:
            verified = classify_package(output, limits=selected_limits)
            if verified.valid and verified.identity.scientific_identity_hash == candidate.identity.scientific_identity_hash:
                return output
        raise FileExistsError("materialization destination contains a different or unverifiable package")
    if output.exists():
        raise FileExistsError("materialization destination exists and is not a directory")
    partial = output.with_name(f".{output.name}.partial")
    if partial.exists():
        if partial.is_dir():
            shutil.rmtree(partial)
        else:
            partial.unlink()
    partial.mkdir(parents=True)
    try:
        with zipfile.ZipFile(candidate.path) as archive:
            from certgen.discovery.security import inspect_zip_central_directory

            inspection = inspect_zip_central_directory(archive, limits=selected_limits)
            if not inspection.passed:
                raise ValueError("selected archive failed safety revalidation: " + "; ".join(inspection.errors))
            for info in archive.infolist():
                target = partial.joinpath(*Path(info.filename).parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("xb") as handle:
                    shutil.copyfileobj(source, handle, 1024 * 1024)
        marker_path = partial / marker.name
        marker_path.write_text(str(candidate.package_sha256) + "\n", encoding="utf-8")
        verified = classify_package(partial, limits=selected_limits)
        if not verified.valid or verified.identity.scientific_identity_hash != candidate.identity.scientific_identity_hash:
            raise ValueError("materialized package failed identity/integrity verification")
        output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(partial, output)
    except Exception:
        if partial.is_dir():
            shutil.rmtree(partial)
        raise
    runtime = {
        "schema_version": "certgen.runtime_location.v1",
        "source_form": candidate.form.value,
        "source_sha256": candidate.package_sha256,
        "scientific_identity_hash": candidate.identity.scientific_identity_hash,
        "claim_allowed": False,
    }
    (output / ".certgen_runtime_location.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


__all__ = [
    "DiscoveryLimits",
    "DiscoveryResult",
    "ExpectedPackageIdentity",
    "PackageCandidate",
    "PackageRequirement",
    "PackageType",
    "SelectionStatus",
    "classify_package",
    "configured_roots",
    "discover_asset_mount",
    "discover_dataset_root",
    "discover_packages",
    "discover_reference",
    "discover_wheelhouse",
    "validate_resolved_asset",
    "write_asset_resolution_report",
    "materialize_selected_package",
]
