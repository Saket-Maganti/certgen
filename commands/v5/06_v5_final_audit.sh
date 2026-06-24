#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
python3 -m certgen.audit.v5_audit --out docs/V5_FINAL_AUDIT.md --json-out data/results/v5_final_audit.json
