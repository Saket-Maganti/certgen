#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.cli.run_v6_execution_gate --stage r1d --feature-dir "${CERTGEN_FEATURE_ROOT:-data/features/cifar10_r1}"
