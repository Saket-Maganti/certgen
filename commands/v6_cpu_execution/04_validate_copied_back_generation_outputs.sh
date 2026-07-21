#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.validate_kaggle_generation_output_zip \
  --input-zip "${CERTGEN_GENERATION_OUTPUT_ZIP:-data/kaggle_outputs/certgen_cifar10_generated_1k_outputs.zip}" \
  --extract-dir "${CERTGEN_GENERATION_EXTRACT_DIR:-data/sources/cifar10_r1/generated_1k}" \
  --out-manifest "${CERTGEN_GENERATED_MANIFEST:-registry/manifests/cifar10_r1_generated_pilot_1000.jsonl}" \
  --summary-out "${CERTGEN_GENERATION_OUTPUT_SUMMARY:-data/results/v6_generation_output_validation_summary.json}" \
  --expected-count-per-model "${CERTGEN_GENERATION_COUNT_PER_MODEL:-1000}"
