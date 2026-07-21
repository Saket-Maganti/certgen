#!/usr/bin/env bash
set -euo pipefail

: "${CERTGEN_R2_ENABLE_50K:?Set CERTGEN_R2_ENABLE_50K=1 only after 10k gates pass and 50k is approved.}"

export PYTHONDONTWRITEBYTECODE=1
export CERTGEN_KAGGLE_WORK_ROOT="${CERTGEN_KAGGLE_WORK_ROOT:-/kaggle/working/r2_50k_features}"
export CERTGEN_R1_SAMPLE_MANIFEST="${CERTGEN_R2_SAMPLE_MANIFEST:-/kaggle/input/certgen/cifar10_r2_50k_feature_extraction_samples.jsonl}"

bash commands/r1c_kaggle_feature_extraction/00_extract_inception_clip_t4x2.sh
