#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.packaging.import_kaggle_generation_outputs --zip "${GENERATION_ZIP:-certgen_cifar10_generation_outputs.zip}" --out-json data/results/v7_generation_import_summary.json
