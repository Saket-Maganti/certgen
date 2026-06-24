# 09 — V5 Execution Runbooks and Command Bundles

## Goal

Make the project ready to execute real pilot runs after V5, while not executing them inside V5.

## Add Files

Create:

- `docs/execution/V5_REAL_PILOT_RUNBOOK.md`
- `docs/execution/V5_COMMAND_BUNDLES.md`
- `commands/v5/00_validate_state.sh`
- `commands/v5/01_validate_provenance_ledger.sh`
- `commands/v5/02_validate_or_materialize_feature_caches.sh`
- `commands/v5/03_reproduce_metric_point_estimate.sh`
- `commands/v5/04_run_first_clean_core_pilot_nonclaim.sh`
- `commands/v5/05_render_pilot_report_card_nonclaim.sh`
- `commands/v5/06_v5_final_audit.sh`
- `certgen/commands/generate_v5_command_bundle.py`
- `tests/test_v5_command_bundle.py`

## Safety Requirements

Every shell script must:

- use `set -euo pipefail`;
- avoid hardcoded user-specific paths;
- accept environment variables or CLI args;
- default to dry-run or validation mode where appropriate;
- refuse to run if required provenance is missing;
- write outputs under documented directories;
- mark outputs `pilot_nonclaim` unless all evidence gates pass.

## Required Command Flow

The runbook should define this exact real-pilot flow:

1. Validate V5 state and claim boundaries.
2. Fill/validate real provenance ledger.
3. Validate or materialize feature caches.
4. Lock preprocessing.
5. Reproduce one reported metric point estimate.
6. Run clean-core certificate pilot in non-claim mode.
7. Render pilot report card.
8. Run V5 audit.
9. Decide whether pilot can be promoted to evidence candidate in a later gate.

## Do Not Execute Real Runs

The command bundle should be generated, documented, and tested with fixtures only. It must not download large real datasets or run GPU jobs by default.

## Tests

Tests should verify:

- scripts exist and are executable or documented;
- scripts contain safety flags;
- command generator emits all steps;
- no script contains `/Users/saketmaganti/` or absolute local paths;
- scripts fail safe when inputs are missing.
