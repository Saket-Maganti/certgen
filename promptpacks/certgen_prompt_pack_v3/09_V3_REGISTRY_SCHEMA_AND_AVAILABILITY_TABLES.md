# Prompt 09 — Registry Schema and Availability Tables

Upgrade the registry from V2 templates into a structured source of truth for benchmark/model-pair availability.

## Goal

Create schema and validation around:

- benchmarks;
- datasets;
- generated sample sources;
- reference real sources;
- feature caches;
- model pairs;
- reported claims;
- pilot eligibility.

Files:

- `registry/v3/benchmarks_template.csv`
- `registry/v3/model_pairs_template.csv`
- `registry/v3/feature_caches_template.csv`
- `certgen/registry/v3_schema.py`
- `certgen/cli/validate_v3_registry.py`
- `docs/V3_REGISTRY_GUIDE.md`

## Pilot eligibility levels

Define:

- `not_checked`
- `availability_planned`
- `samples_available`
- `features_available_unvalidated`
- `features_validated`
- `metric_reproduced`
- `pilot_ready`
- `pilot_blocked`

A comparison can be `pilot_ready` only if:

- public/free sample or feature source verified;
- license is allowed or verified free;
- reference real features available/valid;
- model A features available/valid;
- model B features available/valid;
- feature extractor and preprocessing match;
- metric is clean-core or correctly descriptive;
- published claim row has source metadata if auditing a literature claim.

## CLI

```bash
python3 -m certgen.cli.validate_v3_registry \
  --benchmarks registry/v3/benchmarks_template.csv \
  --model-pairs registry/v3/model_pairs_template.csv \
  --feature-caches registry/v3/feature_caches_template.csv \
  --out docs/V3_REGISTRY_VALIDATION.md \
  --json-out data/results/v3_registry_validation.json
```

## Availability table generation

Add command:

```bash
python3 -m certgen.cli.render_availability_table \
  --registry-dir registry/v3 \
  --out docs/V3_AVAILABILITY_TABLE.md \
  --json-out data/results/v3_availability_table.json
```

The table should show:
- candidate comparisons;
- what is missing;
- next action;
- whether it is pilot-ready;
- claim_allowed=false.

## Tests

- valid templates pass;
- missing model pair fails;
- restricted license blocks;
- preprocessing mismatch blocks;
- pilot-ready requires all gates;
- availability table renders missing items clearly.

## Verification

Run pytest and registry validation on templates.
