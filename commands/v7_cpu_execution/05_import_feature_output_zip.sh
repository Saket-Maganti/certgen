#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.packaging.import_kaggle_feature_outputs --zip "${FEATURE_ZIP:-certgen_cifar10_features_1k_outputs.zip}" --out-json data/results/v7_feature_import_summary.json
