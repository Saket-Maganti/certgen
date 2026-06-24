#!/usr/bin/env bash
set -euo pipefail

# V5 safe command bundle. Defaults are validation/non-claim only.
: "${CERTGEN_PILOT_SUMMARY:?set CERTGEN_PILOT_SUMMARY}"
python3 -m certgen.cli.render_pilot_report --summary-json "$CERTGEN_PILOT_SUMMARY" --out docs/FIRST_REAL_CLEAN_CORE_PILOT_REPORT.md
