#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.validate_kaggle_feature_output_zip \
  --input-zip "${CERTGEN_FEATURE_OUTPUT_ZIP:-data/kaggle_outputs/certgen_cifar10_features_1k_outputs.zip}" \
  --extract-dir "${CERTGEN_FEATURE_EXTRACT_DIR:-data/features/cifar10_r1}" \
  --summary-out "${CERTGEN_FEATURE_OUTPUT_SUMMARY:-data/results/v6_feature_output_validation_summary.json}"
