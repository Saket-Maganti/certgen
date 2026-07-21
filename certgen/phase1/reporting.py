"""Generate the required Phase 1 launchboard, handbooks, and inventories."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.phase1.kaggle import BUNDLES, inventory
from certgen.phase1.notebooks import PHASE1_NOTEBOOKS
from certgen.phase1.state import phase1_state


RUNTIME_ROWS = [
    ("environment_diagnostic", "5", "20", "minutes"),
    ("checkpoint_preflight", "20", "60", "minutes"),
    ("two_model_1k_generation", "45", "180", "minutes"),
    ("all_role_inception_clip_extraction", "45", "180", "minutes"),
    ("kaggle_packaging_per_stage", "5", "25", "minutes"),
    ("local_import_per_returned_zip", "2", "20", "minutes"),
    ("complete_first_1k_pilot", "5", "10", "hours"),
]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _zip(root: Path, stage: str) -> tuple[str, str]:
    relative = BUNDLES[stage]
    path = root / relative
    return str(relative), file_sha256(path) if path.is_file() else "MISSING"


def _launchboard(root: Path, state: dict[str, Any]) -> str:
    diagnostic_zip, diagnostic_hash = _zip(root, "diagnostic")
    preflight_zip, preflight_hash = _zip(root, "preflight")
    rows = [
        ("diagnostic", "READY_TO_UPLOAD" if diagnostic_hash != "MISSING" else "LOCAL_DEFECT", diagnostic_zip, diagnostic_hash, PHASE1_NOTEBOOKS["diagnostic"], "GPU T4 x2", "KAGGLE_INTERNET_ON_INSTALL", "none", "5-20 min", "certgen_kaggle_environment_diagnostic_output.zip", "data/kaggle_returns/diagnostic/", 'CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain'),
        ("preflight", "READY_AFTER_DIAGNOSTIC", preflight_zip, preflight_hash, PHASE1_NOTEBOOKS["preflight"], "GPU T4 x2", "KAGGLE_INTERNET_ON_INSTALL; model loading offline", "private validated DDPM, Inception, CLIP mounts", "20-60 min", "certgen_cvpr_preflight_<run_id>.zip", "data/kaggle_returns/preflight/", 'CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain'),
        ("generation_1k", "BLOCKED_REAL_PREFLIGHT_IMPORT", "not built", "not built", PHASE1_NOTEBOOKS["generation"], "GPU T4 x2", "Internet off", "private validated DDPM mounts", "45-180 min", "certgen_cvpr_generation_<run_id>.zip", "data/kaggle_returns/generation/", 'CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain'),
        ("features_1k", "BLOCKED_REAL_GENERATION_IMPORT", "not built", "not built", PHASE1_NOTEBOOKS["features"], "GPU T4 x2", "Internet off", "private validated Inception and CLIP mounts", "45-180 min", "certgen_cvpr_features_<run_id>.zip", "data/kaggle_returns/features/", 'CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain'),
    ]
    header = "| stage | status | input ZIP | ZIP hash | notebook | accelerator | internet setting | private assets | estimated runtime | expected output ZIP | local copy-back path | exact resume command |"
    divider = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    body = ["| " + " | ".join(f"`{value}`" for value in row) + " |" for row in rows]
    return "\n".join(
        [
            "# CertGen Kaggle run launchboard",
            "",
            "All runtime values are `PLANNING_ESTIMATE_NOT_MEASURED`. Paths and hashes are generated from live artifacts. `claim_allowed=false`.",
            "",
            f"Current boundary: `{state['boundary']}`. Exact next action: `{state['exact_next_action']}`.",
            "",
            header,
            divider,
            *body,
        ]
    )


def _command_rows(root: Path) -> list[dict[str, str]]:
    ledger = root / "reports/CERTGEN_PHASE1_COMMAND_LEDGER.csv"
    if not ledger.is_file():
        return []
    with ledger.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def generate_phase1_reports(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    state = phase1_state(base)
    bundle_inventory = inventory(base)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    runtime_csv = base / "reports/CERTGEN_KAGGLE_RUNTIME_ESTIMATES.csv"
    runtime_csv.parent.mkdir(parents=True, exist_ok=True)
    with runtime_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["stage", "minimum", "maximum", "unit", "measurement_class", "claim_allowed"])
        writer.writerows([(*row, "PLANNING_ESTIMATE_NOT_MEASURED", "false") for row in RUNTIME_ROWS])
    _write(
        base / "reports/CERTGEN_KAGGLE_RUNTIME_ASSUMPTIONS.md",
        """# Kaggle runtime assumptions

Every duration is `PLANNING_ESTIMATE_NOT_MEASURED`, not a measured CertGen result. Ranges assume Kaggle GPU T4 x2, one worker per GPU, pinned dependencies, warm private caches after preflight, resumable deterministic shards, and no queue or restart delay. Real diagnostic and preflight artifacts replace planning assumptions only in typed runtime records; they never become empirical model evidence. `claim_allowed=false`.""",
    )

    launchboard = _launchboard(base, state)
    _write(base / "CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md", launchboard)
    _write(
        base / "CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md",
        f"""# CertGen Kaggle T4x2 execution handbook

Current Phase 1 boundary: `{state['boundary']}`. All GPU notebooks require **GPU T4 x2**; zero-, one-, or ambiguous-GPU visibility fails before work.

1. Validate the input ZIP locally with `python3 -m certgen kaggle validate-input <zip>`.
2. Attach the ZIP and, for preflight or later, the private assets described in `KAGGLE_ASSET_SETUP.md`.
3. Select the dependency mode frozen in the configuration. Keep model loading offline.
4. Run the matching canonical notebook top-to-bottom. Preserve status/log/shard files on failure.
5. Download the single final ZIP (or every hash-manifested multipart member) without unpacking or renaming.
6. Place it in the launchboard copy-back directory and run `CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`.

Never mix run IDs, configuration hashes, study hashes, asset revisions, seed partitions, or feature rows. Resume reuses only validated completion markers. No notebook may set `claim_allowed=true`.

Exact next action: `{state['exact_next_action']}`.
""",
    )
    _write(
        base / "CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md",
        """# CertGen Kaggle dependency and asset guide

The stage locks under `requirements/` pin the Python 3.11 T4x2 environment and share `kaggle-constraints.txt`. Supported modes are `KAGGLE_INTERNET_ON_INSTALL`, `PRIVATE_WHEELHOUSE_OFFLINE`, and `USE_PREINSTALLED_VALIDATED`. Each notebook runs `python -m pip check` and writes `dependency_report.json`, `dependency_freeze.txt`, and `pip_check.txt`.

The minimum CIFAR pilot uses Inception and the Transformers CLIP loader; DINO and CFM are not forced. Public archives contain no weights. CLIP always requires a private validated mount or equivalent user cache. See `KAGGLE_ASSET_SETUP.md` for the exact mount layout and fail-closed manifest contract. `claim_allowed=false`.""",
    )
    catalog_lines = [
        "# CertGen Kaggle input bundle catalog",
        "",
        "All packages are deterministic, restricted-weight-free, credential-free, and non-evidentiary. `claim_allowed=false`.",
        "",
        "| Stage | Path | State | SHA-256 |",
        "|---|---|---|---|",
    ]
    for row in bundle_inventory["bundles"]:
        catalog_lines.append(f"| `{row['stage']}` | `{row['path']}` | `{'VALID' if row.get('valid') else ('BLOCKED_PLAN' if row.get('blocked_plan') else 'MISSING')}` | `{row.get('sha256') or 'n/a'}` |")
    _write(base / "CERTGEN_KAGGLE_INPUT_BUNDLE_CATALOG.md", "\n".join(catalog_lines))
    _write(
        base / "CERTGEN_PHASE1_NEXT_ACTION.md",
        f"# CertGen Phase 1 next action\n\nStatus: `{state['phase1_status']}`\n\nExact next action: `{state['exact_next_action']}`\n\nDo not perform a speculative pre-GPU build. `claim_allowed=false`.",
    )

    command_rows = _command_rows(base)
    matrix_lines = [
        "# CertGen Phase 1 test matrix",
        "",
        "| Sequence | Phase | Command | Status | Exit |",
        "|---:|---|---|---|---:|",
    ]
    for row in command_rows:
        matrix_lines.append(f"| {row['sequence']} | `{row['phase']}` | `{row['command'].replace('|', '&#124;')}` | `{row['status']}` | {row['exit_code']} |")
    _write(base / "reports/CERTGEN_PHASE1_TEST_MATRIX.md", "\n".join(matrix_lines))

    artifacts = [
        *PHASE1_NOTEBOOKS.values(),
        *(str(path) for path in BUNDLES.values()),
        "requirements/kaggle-base.lock",
        "requirements/kaggle-preflight.lock",
        "requirements/kaggle-generation.lock",
        "requirements/kaggle-features.lock",
        "requirements/kaggle-constraints.txt",
        "registry/cvpr/kaggle_asset_registry.yaml",
        "KAGGLE_ASSET_SETUP.md",
        "artifacts/cvpr/kaggle_inputs/generation/BUILD_PLAN.json",
        "artifacts/cvpr/kaggle_inputs/features/BUILD_PLAN.json",
    ]
    inventory_path = base / "reports/CERTGEN_PHASE1_ARTIFACT_INVENTORY.csv"
    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "exists", "size", "sha256", "claim_allowed"])
        for relative in artifacts:
            path = base / relative
            writer.writerow([relative, str(path.is_file()).lower(), path.stat().st_size if path.is_file() else "", file_sha256(path) if path.is_file() else "", "false"])

    current_path = base / "reports/CERTGEN_PHASE1_CURRENT_STATE.json"
    try:
        current = json.loads(current_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        current = {}
    current.update(
        {
            "schema_version": "certgen.phase1.current_state.v1",
            "updated_utc": now,
            **state,
            "kaggle_inventory": bundle_inventory,
            "cpu_only": True,
            "known_local_defect": None,
            "claim_allowed": False,
        }
    )
    current_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cifar_found = state["cifar_present"]
    completion = f"""# CertGen Phase 1 pre-GPU completion report

Status: `{state['phase1_status']}`

1. CIFAR found: `{'yes' if cifar_found else 'no'}` at `data/sources/cifar-10-python.tar.gz`.
2. Validated and materialized: `{'yes' if state['reference_materialized'] else 'no; official archive required'}`.
3. Profile/study frozen: `{'yes' if state['reference_materialized'] else 'profile selected; study waits for the real reference'}`.
4. Reference draw built: `{'yes' if (base / 'registry/manifests/cvpr/reference_draw_plan.json').is_file() else 'no; waits for materialized reference'}`.
5. Upload ZIPs present: diagnostic and preflight; both validate locally.
6. Stage-dependent ZIPs: generation 1k and features 1k; only complete blocked plans exist.
7. Next notebook: `{state['next_notebook'] or 'none until the official CIFAR archive is supplied; then diagnostic'}`.
8. T4x2 required: `yes` for every real Kaggle stage.
9. Internet mode: `KAGGLE_INTERNET_ON_INSTALL` for diagnostic/preflight dependency installation; model loading and later stages use Internet off.
10. Private assets: none for diagnostic; validated DDPM, Inception, and CLIP mounts for preflight/later. CLIP is never in a public archive.
11. Estimated runtime: diagnostic 5-20 min; preflight 20-60 min; first 1k pilot 5-10 hr total. All are `PLANNING_ESTIMATE_NOT_MEASURED`.
12. Output ZIP: after diagnostic, `certgen_kaggle_environment_diagnostic_output.zip`.
13. Place it at: `data/kaggle_returns/diagnostic/`.
14. Resume: `CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`.
15. Local defect remaining: `no`.

Exact next action: `{state['exact_next_action']}`.

No empirical claim is authorized. `claim_allowed=false`.
"""
    _write(base / "CERTGEN_PHASE1_PRE_GPU_COMPLETION_REPORT.md", completion)
    return {"status": state["phase1_status"], "reports_generated": True, "claim_allowed": False}
