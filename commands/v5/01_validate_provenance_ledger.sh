#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
: "${CERTGEN_LEDGER:?set CERTGEN_LEDGER to a real provenance ledger}"
python3 -m certgen.cli.validate_provenance_ledger --ledger "$CERTGEN_LEDGER" --out docs/PROVENANCE_LEDGER_VALIDATION.md --json-out data/results/provenance_ledger_validation.json --allow-missing-local
