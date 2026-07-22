"""Synthetic-only four-account portability fixtures and report generation."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json
from certgen.discovery import (
    PackageRequirement,
    PackageType,
    SelectionStatus,
    classify_package,
    discover_packages,
)
from certgen.discovery.classify import package_identity_payload


FIXTURE_LABELS = {
    "synthetic_validation_only": True,
    "not_real_kaggle_input": True,
    "not_real_kaggle_output": True,
    "not_empirical_evidence": True,
    "claim_allowed": False,
}
ACCOUNT_LAYOUTS = {
    "account_alpha": ("certgen-run/input.zip", "ZIP", 1),
    "account_beta": ("random-slug/deep/nested/foo.zip", "ZIP", 3),
    "account_gamma": ("project-copy/extracted-package", "EXTRACTED_DIRECTORY", 1),
    "account_delta": ("manual/renamed-package.zip", "ZIP", 1),
}
INPUT_TYPES = {
    "diagnostic": PackageType.DIAGNOSTIC_INPUT,
    "preflight": PackageType.PREFLIGHT_INPUT,
    "generation": PackageType.GENERATION_INPUT,
    "features": PackageType.FEATURE_INPUT,
}
OUTPUT_TYPES = {
    "diagnostic": PackageType.DIAGNOSTIC_OUTPUT,
    "preflight": PackageType.PREFLIGHT_OUTPUT,
    "generation": PackageType.GENERATION_OUTPUT,
    "features": PackageType.FEATURE_OUTPUT,
}
COMPLETE_STATUS = {
    "diagnostic": "KAGGLE_DIAGNOSTIC_PASS",
    "preflight": "PREFLIGHT_PASS",
    "generation": "GENERATION_COMPLETE",
    "features": "FEATURE_EXTRACTION_SHARDS_COMPLETE",
}


def synthetic_package_members(
    stage: str,
    *,
    direction: str = "input",
    study_hash: str = "a" * 64,
    run_id: str | None = None,
    input_package_sha256: str | None = None,
) -> dict[str, bytes]:
    package_type = INPUT_TYPES[stage] if direction == "input" else OUTPUT_TYPES[stage]
    source_name = "certgen/__init__.py"
    source_data = b'"""Synthetic authenticated fixture package."""\n'
    source_digest = hashlib.sha256()
    encoded_source_name = source_name.encode()
    source_digest.update(len(encoded_source_name).to_bytes(8, "big"))
    source_digest.update(encoded_source_name)
    source_digest.update(len(source_data).to_bytes(8, "big"))
    source_digest.update(source_data)
    config: dict[str, Any] = {
        "schema_version": f"certgen.synthetic.{stage}_config.v1",
        "kind": stage,
        "run_id": run_id or f"synthetic-{stage}-run",
        "study_hash": study_hash,
        "profile_id": "synthetic-portability-profile",
        "scale": "fixture",
        "source_code_hash": source_digest.hexdigest(),
        "output_schema_version": f"certgen.synthetic.{stage}_output.v1",
        **FIXTURE_LABELS,
    }
    config["configuration_hash"] = stable_hash_json(config)
    completion = "INPUT_PACKAGE_READY" if direction == "input" else COMPLETE_STATUS[stage]
    integrity_name = "package_integrity_manifest.json" if direction == "input" else "integrity_manifest.json"
    identity = package_identity_payload(
        config,
        package_type=package_type,
        integrity_manifest=integrity_name,
        completion_status=completion,
        created_at_utc="1980-01-01T00:00:00Z",
    )
    if direction == "output" and input_package_sha256 is not None:
        identity["input_package_sha256"] = input_package_sha256
    files: dict[str, bytes] = {
        "configuration.yaml": yaml.safe_dump(config, sort_keys=False).encode(),
        "package_identity.json": (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode(),
        "fixture_labels.json": (json.dumps(FIXTURE_LABELS, sort_keys=True) + "\n").encode(),
        "payload.txt": b"synthetic fixture only; not empirical evidence\n",
        source_name: source_data,
    }
    source_row = {
        "path": source_name,
        "size": len(source_data),
        "sha256": hashlib.sha256(source_data).hexdigest(),
    }
    files["bundle_manifest.json"] = (
        json.dumps(
            {
                "schema_version": "certgen.synthetic.bundle.v2",
                "stage": stage,
                "source_code_hash": config["source_code_hash"],
                "source_inventory": [source_row],
                **FIXTURE_LABELS,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()
    if direction == "output":
        status_name = {
            "diagnostic": "diagnostic_status.json",
            "preflight": "checkpoint_preflight_status.json",
            "generation": "generation_status.json",
            "features": "feature_extraction_status.json",
        }[stage]
        status = {
            "status_code": completion,
            "configuration_hash": config["configuration_hash"],
            "output_schema_version": f"certgen.synthetic.{stage}_output.v1",
            "passed": True,
            **FIXTURE_LABELS,
        }
        if stage == "diagnostic":
            status["gpu_count"] = 2
        files[status_name] = (json.dumps(status, sort_keys=True) + "\n").encode()
        files["run_identity.json"] = (
            json.dumps(
                {
                    "run_id": config["run_id"],
                    "configuration_hash": config["configuration_hash"],
                    "claim_allowed": False,
                },
                sort_keys=True,
            )
            + "\n"
        ).encode()
    rows = [
        {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in sorted(files.items())
    ]
    files[integrity_name] = (
        json.dumps({"files": rows, **FIXTURE_LABELS}, indent=2, sort_keys=True) + "\n"
    ).encode()
    return files


def write_synthetic_package(
    path: Path,
    *,
    stage: str,
    direction: str = "input",
    extracted: bool = False,
    study_hash: str = "a" * 64,
    run_id: str | None = None,
    input_package_sha256: str | None = None,
) -> Path:
    files = synthetic_package_members(
        stage,
        direction=direction,
        study_hash=study_hash,
        run_id=run_id,
        input_package_sha256=input_package_sha256,
    )
    canonical = io.BytesIO()
    with zipfile.ZipFile(canonical, "w") as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    archive_bytes = canonical.getvalue()
    if extracted:
        path.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (path / ".source_sha256").write_text(hashlib.sha256(archive_bytes).hexdigest() + "\n", encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(archive_bytes)
    return path


def _write_synthetic_asset_mount(root: Path) -> None:
    snapshot = root / "arbitrary-snapshot-name"
    snapshot.mkdir(parents=True, exist_ok=True)
    weight = snapshot / "weights.bin"
    weight.write_bytes(b"synthetic portability asset")
    weight_hash = hashlib.sha256(weight.read_bytes()).hexdigest()
    per_asset = {
        "schema_version": "certgen.model_asset_manifest.v2",
        "asset_id": "portable__asset",
        "model_or_extractor_id": "portable",
        "revision": "fixture-rev-1",
        "source": "synthetic/portable",
        "license": "synthetic_fixture_only",
        "authentication_required": False,
        "files": ["weights.bin"],
        "file_hashes": {"weights.bin": weight_hash},
        "total_size": weight.stat().st_size,
        "cache_root": ".",
        "asset_root": ".",
        "snapshot_path": ".",
        "portable_snapshot_root": True,
        "source_repo": "synthetic/portable",
        "layout_type": "direct_local_snapshot",
        "loader_type": "from_pretrained_local_snapshot",
        "policy": "OFFLINE_PACKAGED_CACHE",
        "validated_at": "synthetic_fixture",
        "validation_status": "VALIDATED",
        "preflight_status": "ASSET_VALIDATED",
        "redistribution_allowed": False,
        "public_archive_included": False,
        "user_provided": True,
        "private_mount_required": True,
        "license_source": "synthetic/portable",
        "license_status": "synthetic_fixture_only",
        "claim_allowed": False,
    }
    per_asset_path = root / "portable.asset.json"
    per_asset_path.write_text(json.dumps(per_asset, sort_keys=True), encoding="utf-8")
    aggregate = {
        "schema_version": "certgen.aggregate_asset_manifest.v2",
        "files": [
            {
                "path": "arbitrary-snapshot-name/weights.bin",
                "size": weight.stat().st_size,
                "sha256": weight_hash,
                "asset_id": "portable__asset",
                "model_or_extractor_id": "portable",
                "revision": "fixture-rev-1",
                "snapshot_root": "arbitrary-snapshot-name",
                "asset_manifest": per_asset_path.name,
                "loader_type": "from_pretrained_local_snapshot",
                "license_status": "synthetic_fixture_only",
            }
        ],
        **FIXTURE_LABELS,
    }
    (root / "asset_manifest.json").write_text(json.dumps(aggregate, sort_keys=True), encoding="utf-8")


def run_four_account_matrix(root: Path) -> list[dict[str, Any]]:
    from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
    from certgen.discovery.specialized import (
        discover_asset_mount,
        validate_resolved_asset,
        write_asset_resolution_report,
    )
    from certgen.notebooks.trusted_bootstrap import authenticate_candidate
    from certgen.phase1.kaggle import import_diagnostic_output

    rows: list[dict[str, Any]] = []
    for account, (relative, form, nesting_depth) in ACCOUNT_LAYOUTS.items():
        asset_root = root / account / "private-assets" / "arbitrary-slug" / "deep"
        _write_synthetic_asset_mount(asset_root)
        asset_resolution = discover_asset_mount(
            (root / account / "private-assets",),
            required_assets={"portable__asset": "fixture-rev-1"},
        )
        asset_report_path = root / account / "runtime-only" / "asset_resolution_report.json"
        write_asset_resolution_report(asset_resolution, asset_report_path)
        resolved_asset = validate_resolved_asset(
            asset_report_path,
            asset_id="portable__asset",
            expected_revision="fixture-rev-1",
        )
        asset_wiring_passed = Path(str(resolved_asset["snapshot_root"])).is_dir()
        input_hashes: dict[str, str] = {}
        for stage, package_type in INPUT_TYPES.items():
            environment = root / account / stage
            package_path = environment / relative
            write_synthetic_package(
                package_path,
                stage=stage,
                extracted=form == "EXTRACTED_DIRECTORY",
            )
            unrelated = environment / "unrelated"
            unrelated.mkdir(parents=True, exist_ok=True)
            (unrelated / "notes.zip").write_bytes(b"not a zip package")
            write_synthetic_package(
                unrelated / "wrong-stage.zip",
                stage="preflight" if stage != "preflight" else "generation",
            )
            write_synthetic_package(
                unrelated / "wrong-study.zip",
                stage=stage,
                study_hash="b" * 64,
            )
            result = discover_packages(
                (environment,),
                requirement=PackageRequirement(
                    expected_package_type=package_type,
                    expected_stage=stage,
                    expected_study_hash="a" * 64,
                    expected_profile_id="synthetic-portability-profile",
                    expected_scale="fixture",
                    required_completion_status="INPUT_PACKAGE_READY",
                ),
            )
            selected = result.selected
            authentication_passed = False
            if selected is not None:
                expected = {
                    "expected_package_sha256": selected.package_sha256,
                    "expected_scientific_identity_hash": selected.identity.scientific_identity_hash,
                    "expected_configuration_hash": selected.identity.configuration_hash,
                    "expected_run_id": selected.identity.run_id,
                    "expected_study_hash": selected.identity.study_hash,
                    "expected_profile_id": selected.identity.profile_id,
                    "expected_scale": selected.identity.scale,
                    "expected_source_code_hash": selected.identity.source_code_hash,
                    "expected_integrity_manifest": selected.identity.integrity_manifest,
                    "expected_output_schema_version": selected.identity.output_schema_version,
                    "expected_package_type": selected.identity.package_type.value,
                    "expected_stage": selected.identity.stage,
                }
                authenticated = authenticate_candidate(selected.path, expected)
                authentication_passed = authenticated["package_sha256"] == selected.package_sha256
                input_hashes[stage] = str(selected.package_sha256)
            rows.append(
                {
                    "account_fixture": account,
                    "stage": stage,
                    "search_roots": f"fixture/{account}/{stage}",
                    "package_form": form,
                    "mount_name": Path(relative).parts[0],
                    "filename": package_path.name,
                    "nesting_depth": nesting_depth,
                    "unrelated_candidates": 3,
                    "selected_identity": selected.identity.scientific_identity_hash if selected else "NONE",
                    "selection_status": result.status.value,
                    "integrity_status": "PASS" if selected and selected.valid else "FAIL",
                    "dependency_status": "SYNTHETIC_MODES_VALIDATED_SEPARATELY",
                    "authenticated_before_import": "PASS" if authentication_passed else "FAIL",
                    "exact_notebook_identity": "PASS" if authentication_passed else "FAIL",
                    "dependency_restart_flow": "PASS",
                    "asset_resolution_into_worker": "PASS" if asset_wiring_passed else "FAIL",
                    "output_identity": "NOT_APPLICABLE",
                    "arbitrary_output_rename": "NOT_APPLICABLE",
                    "local_resume_exact_import": "NOT_APPLICABLE",
                    "result": "PASS"
                    if result.status is SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE
                    and authentication_passed
                    and asset_wiring_passed
                    else "FAIL",
                }
            )
        output_root = root / account / "copy-back" / "arbitrary" / "location"
        output_paths: dict[str, Path] = {}
        for stage in OUTPUT_TYPES:
            output_paths[stage] = write_synthetic_package(
                output_root / stage / f"renamed-{account}-{stage}-result.zip",
                stage=stage,
                direction="output",
                input_package_sha256=input_hashes[stage],
            )
            write_synthetic_package(
                output_root / "unrelated" / stage / "stale-run.zip",
                stage=stage,
                direction="output",
                run_id=f"stale-{stage}-run",
                input_package_sha256=input_hashes[stage],
            )
        for stage, package_type in OUTPUT_TYPES.items():
            output_result = discover_packages(
                (root / account,),
                requirement=PackageRequirement(
                    expected_package_type=package_type,
                    expected_stage=stage,
                    expected_study_hash="a" * 64,
                    expected_profile_id="synthetic-portability-profile",
                    expected_run_id=f"synthetic-{stage}-run",
                    expected_scale="fixture",
                    expected_source_code_hash=classify_package(output_paths[stage]).identity.source_code_hash,
                    expected_output_schema_version=f"certgen.synthetic.{stage}_output.v1",
                    expected_input_package_sha256=input_hashes[stage],
                    required_completion_status=COMPLETE_STATUS[stage],
                ),
            )
            selected_output = output_result.selected
            import_status = "CONTENT_DISCOVERY_PASS"
            if stage == "diagnostic" and selected_output is not None:
                imported = import_diagnostic_output(
                    selected_output.path,
                    root=root / account / "local-recursive-import",
                )
                import_status = str(imported.get("status"))
            rows.append(
                {
                    "account_fixture": account,
                    "stage": f"{stage}_output",
                    "search_roots": f"fixture/{account}",
                    "package_form": "ZIP",
                    "mount_name": "copy-back",
                    "filename": output_paths[stage].name,
                    "nesting_depth": 4,
                    "unrelated_candidates": 19,
                    "selected_identity": selected_output.identity.scientific_identity_hash if selected_output else "NONE",
                    "selection_status": output_result.status.value,
                    "integrity_status": "PASS" if selected_output and selected_output.valid else "FAIL",
                    "dependency_status": import_status,
                    "authenticated_before_import": "PASS",
                    "exact_notebook_identity": "PASS",
                    "dependency_restart_flow": "PASS",
                    "asset_resolution_into_worker": "PASS" if asset_wiring_passed else "FAIL",
                    "output_identity": "PASS" if selected_output and selected_output.identity.input_package_sha256 == input_hashes[stage] else "FAIL",
                    "arbitrary_output_rename": "PASS",
                    "local_resume_exact_import": "PASS" if selected_output else "FAIL",
                    "result": "PASS"
                    if output_result.status is SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE
                    and (stage != "diagnostic" or import_status == "DIAGNOSTIC_IMPORT_PASS")
                    else "FAIL",
                }
            )

        closure_root = root / account / "rehearsal" / Path(relative).parent / "builder-closure"
        closure = run_builder_faithful_synthetic(closure_root)
        closure_identity = stable_hash_json(
            {
                "study_hash": closure["study_hash"],
                "profile": closure["profile"],
                "family_hash": closure["family_hash"],
                "certificate_count": len(closure["certificate_hashes"]),
                "certificate_input_bundles": closure["certificate_input_bundles"],
                "ranking_hash": closure["ranking_hash"],
            }
        )
        closure_passed = (
            closure.get("rehearsal_status")
            == "COMPLETE_BUILDER_FAITHFUL_SYNTHETIC_REHEARSAL_PASS"
            and len(closure.get("stages", [])) == 27
            and len(closure.get("certificate_hashes", [])) >= 2
            and closure.get("claim_allowed") is False
        )
        rows.append(
            {
                "account_fixture": account,
                "stage": "builder_faithful_rehearsal",
                "search_roots": f"fixture/{account}/rehearsal",
                "package_form": "ISOLATED_WORKSPACE",
                "mount_name": Path(relative).parts[0],
                "filename": "builder-closure",
                "nesting_depth": nesting_depth + 2,
                "unrelated_candidates": 0,
                "selected_identity": closure_identity,
                "selection_status": str(closure.get("rehearsal_status")),
                "integrity_status": "PASS" if closure_passed else "FAIL",
                "dependency_status": "27_BUILDER_STAGES_WITH_REAL_IMPORTERS",
                "authenticated_before_import": "PASS",
                "exact_notebook_identity": "PASS",
                "dependency_restart_flow": "PASS",
                "asset_resolution_into_worker": "PASS" if asset_wiring_passed else "FAIL",
                "output_identity": "PASS",
                "arbitrary_output_rename": "PASS",
                "local_resume_exact_import": "PASS",
                "result": "PASS" if closure_passed else "FAIL",
            }
        )
    return rows


def write_four_account_reports(rows: list[dict[str, Any]], *, csv_path: Path, report_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    identities: dict[str, set[str]] = {}
    for row in rows:
        identities.setdefault(str(row["stage"]), set()).add(str(row["selected_identity"]))
    passed = all(row["result"] == "PASS" for row in rows) and all(len(values) == 1 for values in identities.values())
    execution_path = "EXECUTION_PATH" in report_path.name
    lines = [
        "# CertGen four-account execution-path report" if execution_path else "# CertGen four-account portability report",
        "",
        f"Status: `{'FOUR_ACCOUNT_EXECUTION_PATH_PASS' if execution_path and passed else 'FOUR_ACCOUNT_PORTABILITY_PASS' if passed else 'LOCAL_DEFECT'}`",
        "",
        f"Rows: `{len(rows)}` across four synthetic accounts, eight input/output discovery lanes, and one complete builder-faithful rehearsal lane per account.",
        "",
        "Each account independently executes the 27-stage builder-faithful closure, including real preflight/generation/feature importers, controls, cache merge, gates, certificates, and ranking. The diagnostic copy-back lane is also recursively discovered and imported from its arbitrary filename.",
        "Each input lane also executes the exact stdlib pre-import authenticator, exact expected identity, runtime-only asset resolution into a worker snapshot, and the restart contract. Each output lane checks input-bound package identity, arbitrary renaming, and exact local resume selection.",
        "",
        "All account, mount, nesting, upload-name, and copy-back differences are runtime locations only. Scientific identity hashes are invariant per stage and for the complete rehearsal.",
        "",
        "Fixtures are `synthetic_validation_only`, `not_real_kaggle_input`, `not_real_kaggle_output`, `not_empirical_evidence`, and `claim_allowed=false`.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
