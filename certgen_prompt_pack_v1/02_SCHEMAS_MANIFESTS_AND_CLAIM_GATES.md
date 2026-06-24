# Prompt 02 — Schemas, Manifests, Evidence Status, and Claim Gates

## Objective

Implement the basic contracts that prevent CertGen from turning smoke/mock/planned outputs into paper evidence. This is more important than metrics at V1.

## Required context

Read:

- `CERTGEN_PROJECT_MASTER_CONTEXT.md`
- `00_GLOBAL_RULES_FOR_ALL_PROMPTS.md`
- existing files from Prompt 01

## Implement enums

In `certgen/core/enums.py`, define string enums or literal constants for:

### Evidence status

- `real_evidence_candidate`
- `non_evidence_smoke`
- `non_evidence_mock`
- `non_evidence_synthetic`
- `non_evidence_planned`
- `descriptive_only`

### Metric family

- `fid`
- `kid`
- `mmd`
- `cmmd`
- `fd_dinov2`
- `precision_recall`

### Certificate status

- `certified_a_better`
- `certified_b_better`
- `not_decided_at_budget`
- `invalid_not_evidence`
- `descriptive_only`
- `failed_policy_gate`

### FID rigor status

- `descriptive_only`
- `block_cs_experimental`
- `bias_corrected_experimental`
- `rigorous_proof_required`

In V1, `rigorous_proof_required` must not be allowed to pass as real evidence.

## Implement schema dataclasses

Use dataclasses or pydantic only if already available; prefer dataclasses for minimal dependencies.

Create schemas for:

### DatasetRecord

Fields:

- `dataset_id`
- `name`
- `split`
- `source_url_or_note`
- `license_note`
- `num_items_declared`
- `evidence_status`
- `provenance_hash`

### ModelRecord

Fields:

- `model_id`
- `name`
- `family`
- `sample_source`
- `checkpoint_or_samples_available`
- `license_note`
- `evidence_status`

### FeatureManifest

Fields:

- `feature_manifest_id`
- `dataset_or_model_id`
- `feature_type`
- `num_items`
- `feature_dim`
- `preprocessing`
- `feature_path`
- `hash`
- `evidence_status`

### MetricRecord

Fields:

- `metric_name`
- `metric_family`
- `feature_type`
- `estimator_type`
- `supports_clean_cs`
- `fid_rigor_status`
- `evidence_status`

### ComparisonRecord

Fields:

- `comparison_id`
- `dataset_id`
- `model_a_id`
- `model_b_id`
- `reference_id`
- `metric_name`
- `alpha`
- `max_samples`
- `evidence_status`

### DecisionCertificate

Fields:

- `certificate_id`
- `comparison_id`
- `metric_name`
- `alpha`
- `status`
- `n_at_decision`
- `max_samples`
- `lower`
- `upper`
- `point_estimate`
- `optional_stopping_valid`
- `fid_rigor_status`
- `evidence_status`
- `limitations`
- `provenance`

## Serialization

Implement helpers:

```python
to_json_dict(obj) -> dict
write_json(obj, path)
read_json(path) -> dict
stable_hash_json(obj) -> str
```

Hashes should be deterministic for the same JSON content.

## Evidence gate

Implement `certgen/gates/evidence_gate.py`:

- blocks any `real_evidence_candidate` in smoke mode;
- requires all records in a smoke run to be `non_evidence_smoke`, `non_evidence_mock`, `non_evidence_synthetic`, or `descriptive_only`;
- blocks certificates from being considered evidence if any input manifest is non-evidence.

## Claim gate

Implement `certgen/gates/claim_gate.py`:

It should scan generated markdown/json/text reports and block forbidden claim language in non-evidence contexts.

Forbidden phrases for V1 smoke/non-evidence reports include:

- `we find that`
- `we show that`
- `certified result`
- `paper evidence`
- `real evidence`
- `model a beats model b`
- `published wins are undecided`
- `ranking changes`
- `compute saving`
- `empirical result`

Allowed cautious phrases:

- `smoke artifact`
- `non-evidence`
- `planned`
- `placeholder`
- `toy`
- `contract validation`

## Tests

Add tests that:

1. serialize and deserialize every schema;
2. hash is deterministic;
3. evidence gate blocks real evidence in smoke mode;
4. a certificate built from non-evidence inputs becomes `invalid_not_evidence` or remains `non_evidence_smoke`;
5. claim gate catches forbidden phrases in generated smoke reports;
6. claim gate allows cautious non-evidence wording.

## Acceptance criteria

Run:

```bash
python -m pytest -q
```

Then produce a short `docs/V1_SCHEMA_AND_GATE_REPORT.md` explaining what is implemented, what is blocked, and what is still planned.
