"""Synthetic-only four-account portability fixtures and report generation."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json
from certgen.discovery import PackageRequirement, PackageType, SelectionStatus, discover_packages
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
) -> dict[str, bytes]:
    package_type = INPUT_TYPES[stage] if direction == "input" else OUTPUT_TYPES[stage]
    config: dict[str, Any] = {
        "schema_version": f"certgen.synthetic.{stage}_config.v1",
        "kind": stage,
        "run_id": run_id or f"synthetic-{stage}-run",
        "study_hash": study_hash,
        "profile_id": "synthetic-portability-profile",
        "scale": "fixture",
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
    files: dict[str, bytes] = {
        "configuration.yaml": yaml.safe_dump(config, sort_keys=False).encode(),
        "package_identity.json": (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode(),
        "fixture_labels.json": (json.dumps(FIXTURE_LABELS, sort_keys=True) + "\n").encode(),
        "payload.txt": b"synthetic fixture only; not empirical evidence\n",
    }
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
) -> Path:
    files = synthetic_package_members(stage, direction=direction, study_hash=study_hash, run_id=run_id)
    if extracted:
        path.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
    return path


def run_four_account_matrix(root: Path) -> list[dict[str, Any]]:
    from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
    from certgen.phase1.kaggle import import_diagnostic_output

    rows: list[dict[str, Any]] = []
    for account, (relative, form, nesting_depth) in ACCOUNT_LAYOUTS.items():
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
                    "result": "PASS" if result.status is SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE else "FAIL",
                }
            )
        output_root = root / account / "copy-back" / "arbitrary" / "location"
        output_paths: dict[str, Path] = {}
        for stage in OUTPUT_TYPES:
            output_paths[stage] = write_synthetic_package(
                output_root / stage / f"renamed-{account}-{stage}-result.zip",
                stage=stage,
                direction="output",
            )
            write_synthetic_package(
                output_root / "unrelated" / stage / "stale-run.zip",
                stage=stage,
                direction="output",
                run_id=f"stale-{stage}-run",
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
    lines = [
        "# CertGen four-account portability report",
        "",
        f"Status: `{'FOUR_ACCOUNT_PORTABILITY_PASS' if passed else 'LOCAL_DEFECT'}`",
        "",
        f"Rows: `{len(rows)}` across four synthetic accounts, eight input/output discovery lanes, and one complete builder-faithful rehearsal lane per account.",
        "",
        "Each account independently executes the 27-stage builder-faithful closure, including real preflight/generation/feature importers, controls, cache merge, gates, certificates, and ranking. The diagnostic copy-back lane is also recursively discovered and imported from its arbitrary filename.",
        "",
        "All account, mount, nesting, upload-name, and copy-back differences are runtime locations only. Scientific identity hashes are invariant per stage and for the complete rehearsal.",
        "",
        "Fixtures are `synthetic_validation_only`, `not_real_kaggle_input`, `not_real_kaggle_output`, `not_empirical_evidence`, and `claim_allowed=false`.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
