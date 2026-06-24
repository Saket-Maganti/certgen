#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
: "${CERTGEN_FEATURES:?set CERTGEN_FEATURES to an .npz feature cache}"
: "${CERTGEN_SIDECAR:?set CERTGEN_SIDECAR to the matching sidecar}"
python3 -m certgen.cli.validate_feature_cache --features "$CERTGEN_FEATURES" --sidecar "$CERTGEN_SIDECAR" --out docs/FEATURE_CACHE_VALIDATION.md --json-out data/results/feature_cache_validation.json --strict-hash
