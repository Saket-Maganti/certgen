#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
python3 -m certgen.audit.v5_state_intake --out docs/V5_STATE_INTAKE.md --json-out data/results/v5_state_intake.json
