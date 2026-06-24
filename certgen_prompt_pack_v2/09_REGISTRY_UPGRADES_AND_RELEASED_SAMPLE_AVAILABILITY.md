# Prompt 09 — Registry Upgrades and Released-Sample Availability

## Role

You are making the registry strong enough to support a future literature audit. V2 must know whether a comparison is actually reproducible before it enters a pilot.

## Global rules that apply to this prompt

- Preserve V1 behavior and backward compatibility unless the prompt explicitly asks for a breaking change.
- Do not fabricate real results, benchmark numbers, model rankings, citations, sample availability, or claim language.
- Do not promote smoke, mock, synthetic, fixture, planned, or dry-run outputs into evidence.
- Keep tests CPU-only and small. No GPU job may run inside normal tests.
- Keep heavy imports lazy and optional. The repo must remain usable without torch/torchvision/transformers unless a command explicitly requests feature extraction.
- FID and FD-DINOv2 remain descriptive unless a mathematically valid FID/FD certificate is explicitly implemented and audited. Do not weaken this policy.
- No paid APIs, no paid cloud, no paid datasets, no paid annotation, no hosted inference.
- Mark every generated artifact with evidence status: `smoke_only`, `dry_run_only`, `planned`, `descriptive_only`, or `eligible_after_real_run` as appropriate.
- Every new command must have docs, help text, tests, and an example invocation.
- Every claim-producing path must pass through claim gates.
- If a real run is not executed, output files must explicitly say `NO_REAL_EVIDENCE` or equivalent.
- Do not initialize git, commit, tag, or push.

## Task

Upgrade registry schemas/templates to track released-sample availability, feature availability, reported metric claims, and audit eligibility.

## Required files

Create or update:

```text
registry/templates/candidate_model_pairs_template.csv
registry/templates/reported_metric_claims_template.csv
registry/templates/feature_cache_manifest_template.json
certgen/registry/schemas.py
certgen/registry/validate.py
tests/test_registry_v2.py
docs/V2_REGISTRY_SCHEMA.md
```

## Candidate model pair fields

Include:

- `comparison_id`
- `benchmark_id`
- `model_a_id`
- `model_b_id`
- `paper_or_source_id`
- `reported_metric_name`
- `reported_metric_a`
- `reported_metric_b`
- `reported_sample_size`
- `reported_preprocessing_note`
- `released_samples_a_status`
- `released_samples_b_status`
- `checkpoint_a_status`
- `checkpoint_b_status`
- `feature_cache_status`
- `license_status`
- `audit_eligibility`: `eligible`, `blocked`, `needs_user_verification`
- `blocker_reason`

## Reported metric claims fields

Include:

- `claim_id`
- `comparison_id`
- `metric_name`
- `claimed_winner`
- `reported_value_a`
- `reported_value_b`
- `reported_gap`
- `sample_size`
- `source_reference`
- `recomputed_status`
- `certificate_status`
- `claim_evidence_status`

## Validation rules

Validator must block audit eligibility if:

- released samples/checkpoints are unknown;
- sample size missing;
- metric name missing;
- license/source unknown;
- preprocessing unknown;
- reported values are malformed;
- comparison ID not unique.

## Tests

Add tests for valid and invalid registry rows.

## Documentation

`docs/V2_REGISTRY_SCHEMA.md` must explain how to fill the registry without inventing anything.

## Done criteria

- V2 registry validator passes on templates/smoke rows.
- Incomplete real rows are marked `needs_user_verification`, not silently accepted.
