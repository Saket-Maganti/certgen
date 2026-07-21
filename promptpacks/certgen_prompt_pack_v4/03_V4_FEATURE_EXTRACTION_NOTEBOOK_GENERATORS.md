# 03 — V4 Feature Extraction Notebook Generators

Build notebook generators for Kaggle, Colab, and local CPU/GPU feature extraction.

## Goal

CertGen must stay zero-cost and many-small-run friendly. V4 should generate notebooks/scripts that extract and cache features from user-provided or released sample directories without automatic large downloads in tests.

## Implement

Create:

- `certgen/notebooks/generate_feature_notebook.py`
- `certgen/cli/generate_feature_notebook.py`
- templates under `templates/notebooks/`
- generated examples under `notebooks/generated/` or `docs/notebooks/`
- `docs/FEATURE_EXTRACTION_NOTEBOOKS_V4.md`
- tests that inspect generated notebooks/scripts as text.

## Notebook targets

Generate at least:

1. Kaggle notebook/script for Inception features.
2. Kaggle notebook/script for CLIP features.
3. Kaggle notebook/script for DINOv2 features or a placeholder with optional dependency notes.
4. Local script for validating an existing feature cache.

The generator should accept:

```bash
python3 -m certgen.cli.generate_feature_notebook \
  --plan data/results/v4/real_run_plan.json \
  --target kaggle \
  --feature-extractor inception \
  --out notebooks/generated/kaggle_inception_features.ipynb
```

If `.ipynb` generation is too heavy, emit `.py` notebooks compatible with Kaggle/Colab and document this.

## Notebook safety requirements

The generated notebooks must:

- not require paid APIs;
- not include secrets;
- not auto-download huge datasets unless user explicitly sets a flag;
- read sample paths from environment variables or config;
- write feature caches with schema metadata;
- include preprocessing lock information;
- include hash manifests;
- mark outputs `real_unverified` until validator passes;
- avoid hidden claims.

## Feature cache metadata

Each feature cache should include:

- cache id,
- feature extractor name/version,
- source sample manifest hash,
- preprocessing lock id,
- feature shape,
- dtype,
- n samples,
- created timestamp,
- evidence status,
- claim allowed flag,
- code version if available,
- path redaction status.

## Tests

Add tests that:

- generate a Kaggle script from a toy plan;
- confirm no paid API tokens appear;
- confirm environment variables are used for paths;
- confirm evidence status is initialized as non-claim;
- confirm generated script includes cache validation step.

## Acceptance criteria

- Notebook/script generator works without external dependencies.
- Generated notebook is human-runnable later.
- Tests do not extract real features.
- Feature caches remain non-claim until validated.
