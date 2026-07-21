# Prompt 06 — Pilot Registry and Audit Scaffold

## Objective

Build the scaffolding for the first real CertGen pilot without running it. The pilot registry should track candidate benchmarks, model pairs, released-sample availability, preprocessing requirements, metric claims, and evidence status.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- Prompt 01–05 outputs

## Pilot philosophy

The first real pilot should answer one number:

> On one benchmark, what fraction of contestable reported gaps are not statistically decided under the certificate at standard/sample-reported sizes?

V1 must prepare for this but must not claim the number.

## Create pilot registry schema

In `certgen/pilots/registry.py`, implement schemas/helpers for:

### CandidateBenchmark

- `benchmark_id`
- `name`
- `data_source_note`
- `reference_set_available`
- `license_note`
- `preprocessing_requirements`
- `status`: `planned`, `ready_for_feature_extraction`, `blocked`

### CandidateModelPair

- `pair_id`
- `benchmark_id`
- `model_a_name`
- `model_b_name`
- `reported_metric`
- `reported_a_score`
- `reported_b_score`
- `reported_sample_size`
- `paper_or_source`
- `samples_available`
- `checkpoint_available`
- `feature_stats_available`
- `license_note`
- `contestable_reason`
- `status`

### AuditClaimRecord

- `claim_id`
- `pair_id`
- `claim_text`
- `metric_name`
- `reported_direction`
- `recomputed_direction`
- `certificate_status`
- `decided_at_n`
- `evidence_status`
- `limitations`

## Seed registry templates

Create empty or placeholder templates only:

```text
registry/candidate_benchmarks_template.csv
registry/candidate_model_pairs_template.csv
registry/audit_claims_template.csv
```

Allowed examples may include rows marked `non_evidence_planned`, but do not invent reported scores. Use `TBD` or blank fields.

## CLI commands

Add:

```bash
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
```

`plan_first_pilot` should:

- rank candidates only when enough metadata exists;
- otherwise produce a TODO checklist;
- never invent model pairs or scores;
- explicitly say no pilot result exists.

## First-pilot checklist

Generate `docs/FIRST_PILOT_CHECKLIST.md` with required manual checks:

1. benchmark selected;
2. reference real set available;
3. model A/B samples or checkpoints available;
4. reported metric and sample size verified;
5. preprocessing/interpolation documented;
6. license checked;
7. feature extraction path dry-run tested;
8. clean-core metric chosen;
9. FID status marked descriptive if used;
10. no claim made before certificate run.

## Tests

Add tests that:

1. registry CSV templates parse;
2. missing reported scores remain missing, not fabricated;
3. planned rows are `non_evidence_planned`;
4. `plan_first_pilot` does not claim results;
5. claim gate passes the pilot plan;
6. invalid registry rows are flagged clearly.

## Acceptance criteria

Run:

```bash
python -m pytest -q
python -m certgen.cli.validate_registry --benchmarks registry/candidate_benchmarks_template.csv --pairs registry/candidate_model_pairs_template.csv
python -m certgen.cli.plan_first_pilot --pairs registry/candidate_model_pairs_template.csv --out docs/FIRST_PILOT_PLAN.md
```

Then write `docs/V1_PILOT_REGISTRY_REPORT.md`.
