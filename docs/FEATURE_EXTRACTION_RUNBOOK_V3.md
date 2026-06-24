# Feature Extraction Runbook V3

`NO_REAL_EVIDENCE`

V3 feature extraction commands are dry-run planners by default. They do not download models, datasets, or weights inside tests.

Future Kaggle or local extraction should:

1. Fill the provenance ledger.
2. Build a JSONL input manifest.
3. Run `plan_feature_extraction`.
4. Materialize `.npz` features and a V3 sidecar only with explicit user action.
5. Validate the cache with `validate_feature_cache`.

Extraction alone never permits paper claims.
