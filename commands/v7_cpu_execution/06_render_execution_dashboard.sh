#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.runledger.render_dashboard --ledger data/results/v7_run_ledger.jsonl --out docs/V7_EXECUTION_DASHBOARD.md
