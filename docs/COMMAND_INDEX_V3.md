# Command Index V3

`NO_REAL_EVIDENCE`

## V3 Intake Audit

Purpose: verify post-V2 readiness. Evidence status: `dry_run_only`. Paper claims: no.

```bash
python3 -m certgen.cli.v3_intake_audit --out docs/V3_INTAKE_AUDIT.md --json-out data/results/v3_intake_audit.json
```

## Validate Provenance Ledger

Purpose: validate released-sample/source metadata. Evidence status: `planned_only`. Paper claims: no.

```bash
python3 -m certgen.cli.validate_provenance_ledger --ledger registry/provenance/released_sample_ledger_template.csv --out docs/PROVENANCE_LEDGER_VALIDATION.md --json-out data/results/provenance_ledger_validation.json --allow-missing-local
```

## Validate Feature Cache

Purpose: validate `.npz` features and V3 sidecar. Evidence status: `real_features_validated` only after validation. Paper claims: no.

```bash
python3 -m certgen.cli.validate_feature_cache --features data/smoke/v3/audit/features/reference.npz --sidecar data/smoke/v3/audit/features/reference.v3_sidecar.json --out docs/FEATURE_CACHE_VALIDATION.md --json-out data/results/feature_cache_validation.json --strict-hash
```

## Plan Feature Extraction

Purpose: dry-run extraction plan without heavy downloads. Evidence status: `dry_run_only`. Paper claims: no.

```bash
python3 -m certgen.cli.plan_feature_extraction --input-manifest registry/manifests/first_pilot_samples_template.jsonl --extractor inception_v3_pool3 --out-dir data/features/first_pilot/inception --device auto --batch-size 32 --dry-run --out docs/FEATURE_EXTRACTION_PLAN.md --json-out data/results/feature_extraction_plan.json
```

## Audit Metric Reproduction

Purpose: compare metric code/cache/preprocessing to expected values when supplied. Paper claims: no.

```bash
python3 -m certgen.cli.audit_metric_reproduction --config configs/metric_reproduction_v3_smoke.yaml --out docs/METRIC_REPRODUCTION_AUDIT.md --json-out data/results/metric_reproduction_audit.json
```

## Run First Pilot

Purpose: dry-run or non-claim validated-feature pilot. Paper claims: no by default.

```bash
python3 -m certgen.cli.run_first_pilot --pilot-config configs/first_pilot_v3.yaml --out-dir data/results/first_pilot_v3 --report docs/FIRST_PILOT_V3_REPORT.md --json-out data/results/first_pilot_v3/summary.json
```

## Replay Certificate

Purpose: verify deterministic certificate regeneration.

```bash
python3 -m certgen.cli.replay_certificate --certificate data/results/first_pilot_v3/certificates/smoke_a_vs_b_kid_polynomial.json --out docs/CERTIFICATE_REPLAY_REPORT.md --json-out data/results/certificate_replay.json
```

## Render Pilot Report

Purpose: render claim-safe pilot card.

```bash
python3 -m certgen.cli.render_pilot_report --summary-json data/results/first_pilot_v3/summary.json --out docs/FIRST_PILOT_V3_REPORT.md
```

## Validate V3 Registry

Purpose: validate benchmark/model-pair/cache availability tables.

```bash
python3 -m certgen.cli.validate_v3_registry --benchmarks registry/v3/benchmarks_template.csv --model-pairs registry/v3/model_pairs_template.csv --feature-caches registry/v3/feature_caches_template.csv --out docs/V3_REGISTRY_VALIDATION.md --json-out data/results/v3_registry_validation.json
```

## Render Availability Table

Purpose: show missing metadata and next actions.

```bash
python3 -m certgen.cli.render_availability_table --registry-dir registry/v3 --out docs/V3_AVAILABILITY_TABLE.md --json-out data/results/v3_availability_table.json
```

## Run Optional-Stopping Lab

Purpose: synthetic method diagnostic, not benchmark evidence.

```bash
python3 -m certgen.cli.run_optional_stopping_lab --config configs/optional_stopping_lab_v3.yaml --out docs/OPTIONAL_STOPPING_LAB_V3.md --json-out data/results/optional_stopping_lab_v3.json
```

## V3 Final Audit

Purpose: verify real-pilot readiness infrastructure.

```bash
python3 -m certgen.cli.v3_audit --out docs/V3_FINAL_AUDIT.md --json-out data/results/v3_final_audit.json
```
