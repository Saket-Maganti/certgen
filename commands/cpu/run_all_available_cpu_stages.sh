#!/usr/bin/env bash
set -euo pipefail
export CUDA_VISIBLE_DEVICES=""
export CERTGEN_CPU_ONLY=1
exec python3 scripts/run_all_available_cpu_stages.py "$@"
