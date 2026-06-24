# Command Index V4

`NO_REAL_EVIDENCE`

V4 commands prepare CertGen for a first real pilot. They do not create paper evidence by themselves, and generated reports remain `claim_allowed=false`.

## V4 State Intake

```bash
python3 -m certgen.audit.v4_state_intake --out docs/V4_STATE_INTAKE_AUDIT.md --json-out data/results/v4_state_intake_audit.json
```

## Build Real-Run Plan

```bash
python3 -m certgen.cli.build_real_run_plan --ledger registry/provenance/v4_plan_ledger_template.csv --comparison-id v4_template_pair --out data/results/v4/real_run_plan.json --report docs/V4_REAL_RUN_PLAN.md --requested-budget 32
```

## Generate Feature Notebook Script

```bash
python3 -m certgen.cli.generate_feature_notebook --plan data/results/v4/real_run_plan.json --target kaggle --feature-extractor inception_v3_pool3 --out notebooks/generated/kaggle_inception_features.py
```

## Lock Preprocessing

```bash
python3 -m certgen.cli.lock_preprocessing --name v4_smoke_inception_lock --feature-extractor inception_v3_pool3 --out configs/preprocessing_locks/v4_smoke_inception_lock.json
```

## Run Batch Certificates

```bash
python3 -m certgen.cli.run_batch_certificates --config configs/v4_batch_certificates_smoke.json --out-json data/results/v4/batch_certificates.json --report docs/V4_BATCH_CERTIFICATE_REPORT.md
```

## Build Decidedness Audit

```bash
python3 -m certgen.cli.build_decidedness_audit --batch-json data/results/v4/batch_certificates.json --out-csv data/results/v4/decidedness_audit.csv --out-json data/results/v4/decidedness_audit.json --report docs/V4_DECIDEDNESS_AUDIT.md
```

## Build Ranking Stability Report

```bash
python3 -m certgen.cli.build_ranking_stability_report --batch-json data/results/v4/batch_certificates.json --out docs/V4_RANKING_STABILITY_REPORT.md --json-out data/results/v4/ranking_stability.json
```

## Run First Real Pilot Controller

```bash
python3 -m certgen.cli.run_first_real_pilot --plan data/results/v4/real_run_plan.json --out-dir data/results/v4/first_real_pilot --report docs/V4_FIRST_REAL_PILOT_REPORT.md --dry-run
```

## Validate Reported Claims

```bash
python3 -m certgen.cli.validate_reported_claims --claims registry/reported_metric_claims_v4_smoke.csv --out docs/V4_REPORTED_CLAIM_VALIDATION.md --json-out data/results/v4/reported_claim_traces.json
```

## Build Paper Artifact Specs

```bash
python3 -m certgen.cli.build_paper_artifacts --out-dir data/results/v4/paper_artifacts --report docs/V4_PAPER_ARTIFACTS_REPORT.md
```

## Reviewer Attack Harness

```bash
python3 -m certgen.cli.run_reviewer_attack_harness --out docs/V4_REVIEWER_ATTACK_REPORT.md --json-out data/results/v4/reviewer_attack_harness.json
```

## Validate Reproducibility Capsule

```bash
python3 -m certgen.cli.validate_repro_capsule --out docs/V4_REPRO_CAPSULE_VALIDATION.md --json-out data/results/v4_repro_capsule_validation.json
```

## Run Release Safety Scan

```bash
python3 -m certgen.cli.run_release_safety_scan --out docs/V4_RELEASE_SAFETY_REPORT.md --json-out data/results/v4_release_safety.json
```

## V4 Final Audit

```bash
python3 -m certgen.audit.v4_audit --out docs/V4_FINAL_AUDIT.md --json-out data/results/v4_final_audit.json
```

