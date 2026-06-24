# Command Index V5

`NO_REAL_EVIDENCE`

## Test Suite

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
```

## V5 State Intake

```bash
python3 -m certgen.audit.v5_state_intake --out docs/V5_STATE_INTAKE.md --json-out data/results/v5_state_intake.json
```

## Generate Command Bundle

```bash
python3 -m certgen.commands.generate_v5_command_bundle --out-dir commands/v5
```

## V5 Release Safety Scan

```bash
python3 -m certgen.audit.release_safety_v5 --out docs/release/ANONYMITY_AND_PRIVACY_AUDIT_V5.md --json-out data/results/v5_release_safety.json
```

## V5 Final Audit

```bash
python3 -m certgen.audit.v5_audit --out docs/V5_FINAL_AUDIT.md --json-out data/results/v5_final_audit.json
```

## Real Execution Bundle

The scripts in `commands/v5/` require environment variables for real inputs and fail safe if they are missing.

```bash
commands/v5/00_validate_state.sh
commands/v5/01_validate_provenance_ledger.sh
commands/v5/02_validate_or_materialize_feature_caches.sh
commands/v5/03_reproduce_metric_point_estimate.sh
commands/v5/04_run_first_clean_core_pilot_nonclaim.sh
commands/v5/05_render_pilot_report_card_nonclaim.sh
commands/v5/06_v5_final_audit.sh
```

