# 08 — V4 Literature Audit Ingestion and Claim Trace

Build the infrastructure to trace reported generative-model claims into CertGen audit rows.

## Goal

The paper needs an audit of reported wins. V4 should make claim ingestion systematic and conservative.

## Implement

Create:

- `certgen/literature/claim_schema.py`
- `certgen/literature/claim_ingest.py`
- `certgen/literature/claim_trace.py`
- `certgen/cli/validate_reported_claims.py`
- `registry/reported_metric_claims_v4_template.csv`
- `docs/REPORTED_CLAIM_TRACE_GUIDE_V4.md`
- tests.

## Claim row fields

At minimum:

- `claim_id`
- `paper_title`
- `paper_year`
- `venue_or_source`
- `citation_key`
- `benchmark`
- `dataset_split`
- `metric_name`
- `reported_model_a`
- `reported_model_b`
- `reported_score_a`
- `reported_score_b`
- `reported_direction`
- `reported_sample_size`
- `reported_preprocessing`
- `released_samples_available`
- `checkpoint_available`
- `feature_stats_available`
- `license_status`
- `reproduction_status`
- `certgen_status`
- `evidence_status`
- `claim_allowed`
- `notes`

## Trace object

For each claim, generate a trace:

```json
{
  "claim_id": "...",
  "source": "...",
  "reported_values": {},
  "availability": {},
  "provenance_row": "...",
  "feature_cache_ids": [],
  "preprocessing_lock_id": "...",
  "metric_reproduction_id": "...",
  "certificate_ids": [],
  "decidedness_status": "not_run",
  "claim_allowed": false
}
```

## Important policy

Manual literature extraction is allowed. Automated web scraping is not required and should not be added unless explicitly requested. V4 can create templates, validators, and trace machinery.

## Validation

A claim row is audit-eligible only if:

- it has a clear source;
- metric and benchmark are known;
- sample size is known or explicitly unknown;
- availability status is filled;
- claim_allowed is false until gates pass.

## Acceptance criteria

- CSV template validates.
- Missing reported sample size triggers warning/blocker depending strictness.
- Claim trace links claim → provenance → features → reproduction → certificate.
- No claim trace allows paper evidence before certificate gates.
