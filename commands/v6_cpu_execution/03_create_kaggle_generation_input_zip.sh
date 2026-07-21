#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.build_kaggle_generation_input_zip \
  --provenance-ledger "${CERTGEN_PROVENANCE_LEDGER:-registry/provenance/cifar10_r1_ledger.csv}" \
  --out-zip "${CERTGEN_GENERATION_INPUT_ZIP:-data/kaggle_inputs/certgen_cifar10_generation_1k_input.zip}" \
  --manifest-out "${CERTGEN_GENERATION_INPUT_MANIFEST:-data/results/v6_generation_input_zip_manifest.json}" \
  --sample-count-per-model "${CERTGEN_GENERATION_COUNT_PER_MODEL:-1000}" \
  --include-source-mode "${CERTGEN_GENERATION_INCLUDE_SOURCE_MODE:-minimal}"
