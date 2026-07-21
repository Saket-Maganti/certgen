#!/usr/bin/env bash
set -euo pipefail

: "${CERTGEN_R2_ENABLE_10K:?Set CERTGEN_R2_ENABLE_10K=1 only after R1E audit passes and scale is approved.}"

export PYTHONDONTWRITEBYTECODE=1
export CERTGEN_KAGGLE_WORK_ROOT="${CERTGEN_KAGGLE_WORK_ROOT:-/kaggle/working/r2_10k_features}"
export CERTGEN_R1_SAMPLE_MANIFEST="${CERTGEN_R2_SAMPLE_MANIFEST:-/kaggle/input/certgen/cifar10_r2_10k_feature_extraction_samples.jsonl}"

bash commands/r1c_kaggle_feature_extraction/00_extract_inception_clip_t4x2.sh
