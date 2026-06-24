#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
: "${CERTGEN_METRIC_REPRO_CONFIG:?set CERTGEN_METRIC_REPRO_CONFIG}"
python3 -m certgen.cli.audit_metric_reproduction --config "$CERTGEN_METRIC_REPRO_CONFIG" --out docs/METRIC_REPRODUCTION_AUDIT.md --json-out data/results/metric_reproduction_audit.json
