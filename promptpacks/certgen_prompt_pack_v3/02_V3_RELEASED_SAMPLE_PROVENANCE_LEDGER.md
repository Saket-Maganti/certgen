# Prompt 02 — Released-Sample Provenance Ledger

Implement a provenance ledger for released generated samples, reference real sets, model pairs, and published metric claims.

## Goal

CertGen can only audit real model comparisons if each comparison is backed by verified public/free samples, features, or reproducible checkpoints.

Create:

- `certgen/registry/provenance.py`
- `certgen/cli/validate_provenance_ledger.py`
- `registry/provenance/released_sample_ledger_template.csv`
- `docs/PROVENANCE_LEDGER_GUIDE.md`

## Ledger fields

The ledger should support CSV and JSONL.

Required fields:

- `row_id`
- `benchmark_id`
- `dataset_name`
- `dataset_split`
- `reference_source_type` (`public_dataset`, `local_user_provided`, `precomputed_features`)
- `reference_uri_or_path`
- `model_id`
- `model_family`
- `sample_source_type` (`released_samples`, `checkpoint_generated_later`, `precomputed_features`, `unavailable`)
- `sample_uri_or_path`
- `sample_count_available`
- `feature_cache_path`
- `feature_extractor`
- `preprocessing_id`
- `reported_metric_name`
- `reported_metric_value`
- `reported_sample_count`
- `reported_source_title`
- `reported_source_url_or_doi`
- `license_status` (`verified_free`, `unknown`, `restricted`, `not_allowed`)
- `download_required` (`true`, `false`)
- `requires_gpu_to_materialize` (`true`, `false`)
- `verified_by`
- `verified_date`
- `notes`

## Validation rules

Fail hard if:
- required fields are missing;
- `license_status=restricted` or `not_allowed`;
- `sample_source_type=unavailable` for a row requested for real pilot;
- `reported_metric_value` is non-numeric when required;
- `sample_count_available < reported_sample_count` unless explicitly allowed;
- `feature_extractor` conflicts with metric family;
- `preprocessing_id` missing;
- paths are claimed local but missing, unless `--allow-missing-local` is set.

Warn if:
- license unknown;
- source URL/DOI absent;
- sample count unknown;
- generated-later checkpoint needed;
- reported preprocessing is unknown.

## Evidence behavior

Ledger validation alone must produce:

```json
"evidence_status": "planned_only",
"claim_allowed": false
```

because it verifies availability, not results.

## CLI

```bash
python3 -m certgen.cli.validate_provenance_ledger \
  --ledger registry/provenance/released_sample_ledger_template.csv \
  --out docs/PROVENANCE_LEDGER_VALIDATION.md \
  --json-out data/results/provenance_ledger_validation.json \
  --allow-missing-local
```

## Tests

Add fixture ledgers:
- valid planned ledger;
- missing required fields;
- restricted license;
- unavailable samples;
- unknown license warning;
- path missing with and without `--allow-missing-local`.

## Docs

The guide must tell the user how to manually fill the ledger for the first benchmark. Include a “do not fake rows” warning.

## Verification

Run pytest and the CLI on the template ledger.
