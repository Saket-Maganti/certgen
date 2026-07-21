#!/usr/bin/env bash
set -euo pipefail

: "${CERTGEN_R2_ENABLE_50K:?Set CERTGEN_R2_ENABLE_50K=1 only after 10k gates pass and 50k is approved.}"

export PYTHONDONTWRITEBYTECODE=1
export CERTGEN_R2_COUNT_PER_MODEL="${CERTGEN_R2_COUNT_PER_MODEL:-50000}"
export CERTGEN_KAGGLE_WORK_ROOT="${CERTGEN_KAGGLE_WORK_ROOT:-/kaggle/working/r2_50k}"

bash commands/r2_kaggle_generation/00_generate_10000_per_model_t4x2.sh
