# Feature Cache Contract V3

`NO_REAL_EVIDENCE`

Feature caches use `.npz` with a `features` array and a JSON sidecar. The sidecar records cache ID, benchmark ID, model ID, split, extractor, feature dimension, sample count, preprocessing, source, hashes, creator, timestamp, and CertGen version.

Validation can mark features `real_features_validated`, but claim allowance remains false.
