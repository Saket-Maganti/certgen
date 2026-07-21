# Sanity-gate report

Status: `PENDING_REAL_FEATURES` (not a failure).

The implementation now performs measured repeated-batching extraction over identical ordered inputs, measured one-shard versus two-shard merging, and a frozen clean plus three-level Gaussian-blur ladder. Control manifests preserve source, draw, study, preprocessing, corruption, and seed lineage. Synthetic contract tests pass, but no real feature output has been imported, so no real gate result or control certificate exists. `claim_allowed=false`.
