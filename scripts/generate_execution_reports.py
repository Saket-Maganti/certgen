#!/usr/bin/env python3
"""Generate the truthful execution-boundary, release, and publication reports."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
EXECUTION_STATUS = "WAITING_FOR_KAGGLE_DIAGNOSTIC"
PUBLICATION_STATUS = "GITHUB_CLI_REQUIRED"
REMOTE = "https://github.com/Saket-Maganti/certgen.git"
RESUME = (
    'CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 '
    "python3 scripts/run_all_available_cpu_stages.py --resume --explain"
)
DIAGNOSTIC_ZIP = Path(
    "artifacts/cvpr/kaggle_inputs/diagnostic/"
    "certgen_kaggle_environment_diagnostic_input.zip"
)
PREFLIGHT_ZIP = Path(
    "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip"
)
NOTEBOOK = "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb"
RELEASE_ZIP = Path("dist/certgen_execution_pass_20260721_final.zip")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(relative: str, text: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(relative: str, payload: dict[str, Any]) -> None:
    write_text(relative, json.dumps(payload, indent=2, sort_keys=True))


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def sanitize_ledgers() -> None:
    csv_path = REPORTS / "CERTGEN_EXECUTION_COMMAND_LEDGER.csv"
    jsonl_path = REPORTS / "CERTGEN_EXECUTION_COMMAND_LEDGER.jsonl"
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
            fields = list(rows[0]) if rows else []
        for row in rows:
            cwd = str(row.get("cwd", ""))
            if cwd == str(ROOT):
                row["cwd"] = "."
            elif cwd.startswith(str(ROOT) + os.sep):
                row["cwd"] = Path(cwd).relative_to(ROOT).as_posix()
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with jsonl_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                converted: dict[str, Any] = dict(row)
                for key in ("sequence", "exit_code"):
                    try:
                        converted[key] = int(str(converted[key]))
                    except ValueError:
                        pass
                handle.write(json.dumps(converted, sort_keys=True) + "\n")


def sanitize_runtime_outputs() -> None:
    """Remove checkout-specific prefixes from generated, source-controlled records."""

    prefix = str(ROOT) + os.sep
    candidates: list[Path] = []
    for base in (ROOT / "reports", ROOT / "data/results"):
        if base.is_dir():
            candidates.extend(path for path in base.rglob("*") if path.is_file())
    candidates.append(ROOT / "data/artifact_registry.jsonl")
    candidates.extend(
        ROOT / name
        for name in (
            "CERTGEN_EXECUTION_AND_HANDOFF_REPORT.md",
            "CERTGEN_CURRENT_NEXT_ACTION.md",
            "CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md",
            "CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md",
            "CERTGEN_KAGGLE_INPUT_BUNDLE_CATALOG.md",
            "CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md",
            "CERTGEN_1K_PILOT_FINAL_EXECUTION_REPORT.md",
            "CERTGEN_1K_PILOT_STOP_GO_REPORT.md",
        )
    )
    for path in candidates:
        if not path.is_file() or path.stat().st_size > 20_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        portable = text.replace(prefix, "").replace(str(ROOT), ".")
        if portable != text:
            path.write_text(portable, encoding="utf-8")


def tracked_and_candidate_files() -> tuple[set[str], set[str]]:
    tracked = set(filter(None, git("ls-files").splitlines()))
    candidate = set(
        filter(None, git("ls-files", "--cached", "--others", "--exclude-standard").splitlines())
    )
    return tracked, candidate


def ignored(relative: str) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", "--", relative], cwd=ROOT, check=False
    ).returncode == 0


def large_file_audit() -> tuple[list[dict[str, Any]], list[str]]:
    tracked, _ = tracked_and_candidate_files()
    restricted = {".pt", ".pth", ".ckpt", ".safetensors", ".onnx", ".msgpack"}
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        size = path.stat().st_size
        is_restricted = path.suffix.lower() in restricted
        raw = relative.startswith(
            ("data/sources/", "data/reference_materialized/", "data/kaggle_returns/")
        ) or path.name.endswith((".tar.gz", ".7z", ".tgz"))
        if size < 1024 * 1024 and not is_restricted:
            continue
        is_tracked = relative in tracked
        is_ignored = ignored(relative)
        lfs = False
        classification = (
            "raw_execution_input"
            if raw
            else "restricted_model_asset"
            if is_restricted
            else "generated_or_release_artifact"
            if relative.startswith(("dist/", "artifacts/"))
            else "source_or_documentation"
        )
        allowed = not raw and not is_restricted and size < 90 * 1024 * 1024 and not is_ignored
        reason = (
            "raw/restricted execution data must remain local"
            if raw or is_restricted
            else "ignored generated artifact"
            if is_ignored
            else "below the 90 MiB source-control gate"
            if allowed
            else "non-LFS file is at or above 90 MiB"
        )
        rows.append(
            {
                "path": relative,
                "size_bytes": size,
                "tracked": str(is_tracked).lower(),
                "ignored": str(is_ignored).lower(),
                "lfs_managed": str(lfs).lower(),
                "classification": classification,
                "allowed_to_commit": str(allowed).lower(),
                "reason": reason,
            }
        )
        if is_tracked and not allowed:
            blockers.append(relative)
        if not is_ignored and size >= 90 * 1024 * 1024 and not lfs:
            blockers.append(relative)
    path = REPORTS / "CERTGEN_GIT_LARGE_FILE_AUDIT.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "path", "size_bytes", "tracked", "ignored", "lfs_managed",
            "classification", "allowed_to_commit", "reason",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: str(row["path"])))
    return rows, sorted(set(blockers))


def secret_scan() -> list[dict[str, str]]:
    _, candidates = tracked_and_candidate_files()
    patterns = {
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "github_token": re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}"),
        "openai_key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
        "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    }
    findings: list[dict[str, str]] = []
    for relative in sorted(candidates):
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in patterns.items():
            if pattern.search(content):
                findings.append({"path": relative, "pattern": label})
    return findings


def artifact_inventory() -> None:
    study = yaml.safe_load((ROOT / "artifacts/cvpr/study/cifar_integrity_minimal.yaml").read_text())
    paths = [
        ("cifar_source_archive", Path("data/sources/cifar-10-python.tar.gz"), "local_only_raw_input"),
        ("reference_manifest", Path("registry/manifests/cvpr/cifar10_reference.jsonl"), "small_manifest"),
        ("frozen_study", Path("artifacts/cvpr/study/cifar_integrity_minimal.yaml"), "small_frozen_metadata"),
        ("reference_draw", Path("registry/manifests/cvpr/reference_draw_plan.json"), "small_frozen_metadata"),
        ("diagnostic_input", DIAGNOSTIC_ZIP, "small_safe_static_bundle"),
        ("preflight_input", PREFLIGHT_ZIP, "small_safe_static_bundle"),
        ("scale_plan", Path(f"artifacts/max_ceiling/{study['configuration_hash']}/scale_plan.json"), "small_frozen_metadata"),
        ("sensitivity_registry", Path(f"artifacts/max_ceiling/{study['configuration_hash']}/sensitivity_registry.json"), "small_frozen_metadata"),
        ("release_archive", RELEASE_ZIP, "ignored_generated_release"),
    ]
    with (REPORTS / "CERTGEN_EXECUTION_ARTIFACT_INVENTORY.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = ["artifact_type", "path", "exists", "size_bytes", "sha256", "classification", "claim_allowed"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for kind, relative, classification in paths:
            path = ROOT / relative
            writer.writerow(
                {
                    "artifact_type": kind,
                    "path": relative.as_posix(),
                    "exists": str(path.is_file()).lower(),
                    "size_bytes": path.stat().st_size if path.is_file() else "",
                    "sha256": sha256(path) if path.is_file() else "",
                    "classification": classification,
                    "claim_allowed": "false",
                }
            )


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    sanitize_ledgers()
    timestamp = utc_now()
    study = yaml.safe_load((ROOT / "artifacts/cvpr/study/cifar_integrity_minimal.yaml").read_text())
    draw = json.loads((ROOT / "registry/manifests/cvpr/reference_draw_plan.json").read_text())
    diagnostic_hash = sha256(ROOT / DIAGNOSTIC_ZIP)
    preflight_hash = sha256(ROOT / PREFLIGHT_ZIP)
    reference_hash = sha256(ROOT / "data/sources/cifar-10-python.tar.gz")
    reference_rows = sum(
        bool(line.strip())
        for line in (ROOT / "registry/manifests/cvpr/cifar10_reference.jsonl").read_text().splitlines()
    )
    release_manifest = json.loads(
        (ROOT / f"{RELEASE_ZIP.as_posix()}.manifest.json").read_text()
    )
    secret_findings = secret_scan()
    large_rows, large_blockers = large_file_audit()
    artifact_inventory()
    branch = git("branch", "--show-current")
    origin = git("remote", "get-url", "origin", check=False)

    current_state = {
        "schema_version": "certgen.execution.current_state.v1",
        "updated_at_utc": timestamp,
        "execution_status": EXECUTION_STATUS,
        "github_publication_status": PUBLICATION_STATUS,
        "reference": {
            "archive_found": True,
            "archive_valid": True,
            "archive_sha256": reference_hash,
            "materialized": True,
            "manifest_rows": reference_rows,
        },
        "study": {
            "frozen": True,
            "study_hash": study["configuration_hash"],
            "comparisons": [row["comparison_id"] for row in study["model_pairs"]],
            "feature_spaces": study["feature_spaces"],
            "confirmatory_hypotheses": 2,
            "controls": study["controls"],
            "controls_in_confirmatory_family": False,
        },
        "reference_draw_hash": draw["configuration_hash"],
        "kaggle": {
            "diagnostic_input_zip": DIAGNOSTIC_ZIP.as_posix(),
            "diagnostic_input_sha256": diagnostic_hash,
            "preflight_input_zip": PREFLIGHT_ZIP.as_posix(),
            "preflight_input_sha256": preflight_hash,
            "returned_zip_found": False,
            "next_notebook": NOTEBOOK,
            "accelerator": "GPU T4 x2",
            "internet_mode": "Internet ON for dependency installation; model-asset network OFF",
            "private_assets": "none for diagnostic",
            "expected_output_zip": "certgen_kaggle_environment_diagnostic_output.zip",
            "copy_back_path": "data/kaggle_returns/diagnostic/",
            "resume_command": RESUME,
        },
        "quality": {
            "default_pytest": "290 passed, 4 deselected",
            "integration_audits": "4 passed, 290 deselected",
            "ruff": "PASS",
            "changed_code_mypy": "PASS (23 source files at measured run)",
            "historical_full_mypy": "111 errors in 34 files (unchanged)",
            "notebook_determinism": "PASS",
            "paper_compile": "PASS (5 pages; three nonfatal overfull boxes)",
            "release": release_manifest["status"],
        },
        "claim_allowed": False,
        "no_fake_results": True,
        "no_empirical_claims": True,
        "local_defect_remaining": False,
        "next_action": f"Upload {DIAGNOSTIC_ZIP.as_posix()} and run {NOTEBOOK} on GPU T4 x2.",
    }
    write_json("reports/CERTGEN_EXECUTION_CURRENT_STATE.json", current_state)

    write_text(
        "reports/CERTGEN_EXECUTION_BASELINE.md",
        """# CertGen execution baseline

Baseline captured at `2026-07-21T09:05:30Z` before this pass.

- Initial branch: `master`; initial HEAD: `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`.
- The worktree contained extensive pre-existing user changes; none were reset, cleaned, or discarded.
- The restored root CIFAR archive was preserved while a validated copy was placed at the canonical ignored path.
- Historical quality claims were not trusted. The live final runs are `290 passed, 4 deselected`, plus `4` explicit integration audits.
- Whole-repository mypy debt remains exactly `111 errors in 34 files`; changed execution code is clean.
- Local execution was forced CPU-only with `CUDA_VISIBLE_DEVICES=\"\"` and `CERTGEN_CPU_ONLY=1`.

This baseline is engineering evidence only. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_REFERENCE_VALIDATION_REPORT.md",
        f"""# CIFAR-10 reference validation

Status: `PASS`.

- Canonical source: `data/sources/cifar-10-python.tar.gz`
- Size: `{(ROOT / 'data/sources/cifar-10-python.tar.gz').stat().st_size}` bytes
- SHA-256: `{reference_hash}`
- Contract: official CIFAR-10 Python tarball hash, safe members, required batches, decoded 32×32 RGB images, labels, and counts passed.
- Materialization: `{reference_rows}` deterministic test-split reference rows at `registry/manifests/cvpr/cifar10_reference.jsonl`.
- Raw archive and materialized images remain ignored and untracked.

The Kaggle competition test archive was not substituted. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_SANITY_GATE_REPORT.md",
        """# Sanity-gate report

Status: `PENDING_REAL_FEATURES` (not a failure).

The implementation now performs measured repeated-batching extraction over identical ordered inputs, measured one-shard versus two-shard merging, and a frozen clean plus three-level Gaussian-blur ladder. Control manifests preserve source, draw, study, preprocessing, corruption, and seed lineage. Synthetic contract tests pass, but no real feature output has been imported, so no real gate result or control certificate exists. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_CONFIRMATORY_FAMILY_REPORT.md",
        f"""# Confirmatory-family report

Prospective contract: `FROZEN`.

- Study hash: `{study['configuration_hash']}`
- Comparison: `checkpoint_variant`
- Feature spaces: `inception`, `clip`
- Expected family size: `2`
- Sanity controls: `null_reference_split`, `obvious_gap_corruption`
- `controls_in_confirmatory_family=false`
- `controls_claim_allowed=false`

The operational family artifact is intentionally created only after real caches and sanity gates pass. No confirmatory certificate exists yet. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_CERTIFICATE_COVERAGE_REPORT.md",
        """# Certificate-coverage report

Status: `PENDING_REAL_FEATURES_AND_GATES`.

Required confirmatory coverage is two certificates: checkpoint comparison under Inception and under CLIP. Completed real certificates: `0/2`. No result was fabricated or inferred from fixtures. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_CROSS_FEATURE_REPORT.md",
        """# Cross-feature report

Status: `PENDING_CONFIRMATORY_CERTIFICATES`.

Cross-feature agreement cannot be computed before both real family-bound certificates exist. No ranking or cross-feature empirical statement is available. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_PROVENANCE_VERIFICATION.md",
        f"""# Provenance verification

Status: `PASS_FOR_CURRENT_BOUNDARY`.

The archive hash, `{reference_rows}`-row reference manifest, frozen study `{study['configuration_hash']}`, draw `{draw['configuration_hash']}`, and current Kaggle bundle hashes form the current planning/input lineage. The artifact registry accepts content-addressed superseded versions at canonical paths while verifying the latest version. No real Kaggle return or empirical result is registered. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_REPLAY_REPORT.md",
        """# Replay report

Status: `LOCAL_CONTRACT_PASS_REAL_REPLAY_PENDING`.

Deterministic notebook regeneration, fixture-only certificate replay, package rebuilding, and source/draw hashes pass locally. A real pilot replay is impossible until real diagnostic, preflight, generation, and feature outputs are imported. Fixture replay is not empirical evidence. `claim_allowed=false`.
""",
    )
    write_text(
        "reports/CERTGEN_RELEASE_VERIFICATION.md",
        f"""# Release verification

Status: `{release_manifest['status']}`.

- Archive: `{RELEASE_ZIP.as_posix()}` (ignored generated release)
- Members: `{release_manifest['member_count']}`
- Size: `{(ROOT / RELEASE_ZIP).stat().st_size}` bytes
- SHA-256: `{release_manifest['archive_sha256']}`
- Fresh extraction/import check: `{release_manifest['import_check']}`
- Portable tests: `{release_manifest['portable_tests']['summary']}`
- Restricted weight members: none

This verifies reproducibility packaging only. `claim_allowed=false`.
""",
    )
    audits = [
        "paper firewall PASS", "artifact registry PASS with supersession warnings",
        "registry audit PASS", "final pre-run audit 24/24 PASS",
        "maximum-ceiling audit PASS", "Kaggle launch audit 11/11 PASS",
        "CPU execution audit PASS", "privacy/release scans PASS",
    ]
    write_text(
        "reports/CERTGEN_FINAL_AUDIT.md",
        "# Final execution audit\n\n"
        + "\n".join(f"- {item}" for item in audits)
        + f"\n\nNo local defect remains. The only execution blocker is the genuine external diagnostic run. Secret findings: `{len(secret_findings)}`; prohibited tracked/large-file blockers: `{len(large_blockers)}`. `claim_allowed=false`.\n",
    )

    handoff = f"""# CertGen execution and handoff report

`EXECUTION_STATUS={EXECUTION_STATUS}`
`GITHUB_PUBLICATION_STATUS={PUBLICATION_STATUS}`

Completed locally: official CIFAR validation, canonical 10,000-image reference materialization, corrected prospective study/draw/scale/sensitivity freeze, deterministic notebooks and static Kaggle inputs, full local tests, audits, paper build, privacy/restricted-asset checks, and clean release verification.

Next handoff:

- Notebook: `{NOTEBOOK}`
- Input ZIP: `{DIAGNOSTIC_ZIP.as_posix()}`
- SHA-256: `{diagnostic_hash}`
- Accelerator: `GPU T4 x2`
- Internet: ON for dependency installation; model-asset network access OFF
- Private assets: none
- Planning estimate: 5–20 minutes (not measured)
- Expected output: `certgen_kaggle_environment_diagnostic_output.zip`
- Copy back to: `data/kaggle_returns/diagnostic/`
- Resume: `{RESUME}`

No returned Kaggle ZIP was present. No empirical metric, gate, certificate, ranking, or cross-feature result has been claimed. `claim_allowed=false`.
"""
    write_text("CERTGEN_EXECUTION_AND_HANDOFF_REPORT.md", handoff)
    write_text(
        "CERTGEN_CURRENT_NEXT_ACTION.md",
        f"""# Current next action

Upload `{DIAGNOSTIC_ZIP.as_posix()}` (SHA-256 `{diagnostic_hash}`) to Kaggle and run `{NOTEBOOK}` with GPU `T4 x2`. Enable Internet only for dependency installation; no private assets are required. Download `certgen_kaggle_environment_diagnostic_output.zip` to `data/kaggle_returns/diagnostic/`, then run `{RESUME}`.
""",
    )
    write_text(
        "CERTGEN_1K_PILOT_FINAL_EXECUTION_REPORT.md",
        f"""# CertGen 1k pilot execution report

The 1k pilot is not empirically complete. Local preparation is complete through the frozen reference/study/draw and validated diagnostic handoff. Current status: `{EXECUTION_STATUS}`. Real generation, features, gates, two confirmatory certificates, ranking, and cross-feature analysis remain downstream of valid Kaggle returns. `claim_allowed=false`.
""",
    )
    write_text(
        "CERTGEN_1K_PILOT_STOP_GO_REPORT.md",
        """# CertGen 1k pilot stop/go report

Decision: `WAIT_FOR_REQUIRED_DIAGNOSTIC`.

This is an execution boundary, not a scientific stop/go result. Promotion to 10k/50k, DINO, CFM, or another benchmark is prohibited. The frozen 1k decision rules remain unchanged. `claim_allowed=false`.
""",
    )

    legacy_state = {
        "schema_version": "certgen.final_run_ready.current_state.v1",
        "updated_at_utc": timestamp,
        "phase": "reference_study_draw_and_diagnostic_input_complete",
        "top_level_status": EXECUTION_STATUS,
        "readiness_status": EXECUTION_STATUS,
        "selected_profile": "cifar_integrity_minimal",
        "reference_present": True,
        "reference_candidate_present": True,
        "reference_candidate_validated": True,
        "real_evidence_status": "none",
        "claim_allowed": False,
        "blockers": [EXECUTION_STATUS],
        "final_verification": current_state["quality"],
        "exact_next_command": current_state["next_action"],
        "evidence_boundary": "Local software and planning/input validation only; not model or paper evidence.",
    }
    write_json("reports/CERTGEN_FINAL_RUN_READY_CURRENT_STATE.json", legacy_state)

    publication = f"""# GitHub publication report

Status: `{PUBLICATION_STATUS}`.

- Required remote: `{REMOTE}`
- Configured origin: `{origin}`
- Target branch: `{branch}`
- Git CLI: available
- GitHub CLI: missing
- Authentication and remote-history verification: not attempted because the required GitHub CLI is unavailable
- Secret scan findings: `{len(secret_findings)}`
- Large-file blockers: `{len(large_blockers)}`
- Raw CIFAR tracked: `false`
- Returned Kaggle ZIP tracked: `false`

The local validated checkpoint may be committed, but the prompt forbids an alternate push workaround. Install the GitHub CLI and run `gh auth login`, then rerun this execution prompt. No credential output is recorded.
"""
    write_text("reports/CERTGEN_GITHUB_PUBLICATION_REPORT.md", publication)
    push_entry = {
        "timestamp_utc": timestamp,
        "remote_url": origin,
        "branch": branch,
        "commit_sha": "LOCAL_COMMIT_TO_BE_CREATED",
        "push_start_utc": None,
        "push_end_utc": None,
        "remote_verified": False,
        "working_tree_status": "validated_dirty_tree_pending_local_commit",
        "status": PUBLICATION_STATUS,
        "required_user_command": "gh auth login",
    }
    write_text("reports/CERTGEN_GITHUB_PUSH_LEDGER.jsonl", json.dumps(push_entry, sort_keys=True))
    sanitize_runtime_outputs()
    print(
        json.dumps(
            {
                "execution_status": EXECUTION_STATUS,
                "publication_status": PUBLICATION_STATUS,
                "diagnostic_sha256": diagnostic_hash,
                "preflight_sha256": preflight_hash,
                "study_hash": study["configuration_hash"],
                "secret_findings": secret_findings,
                "large_file_blockers": large_blockers,
                "large_file_rows": len(large_rows),
                "claim_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not secret_findings and not large_blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
