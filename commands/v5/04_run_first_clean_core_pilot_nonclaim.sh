#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
: "${CERTGEN_PILOT_CONFIG:?set CERTGEN_PILOT_CONFIG}"
python3 -m certgen.cli.run_first_pilot --pilot-config "$CERTGEN_PILOT_CONFIG" --out-dir data/results/first_real_clean_core_pilot --report docs/FIRST_REAL_CLEAN_CORE_PILOT_REPORT.md --json-out data/results/first_real_clean_core_pilot/summary.json
