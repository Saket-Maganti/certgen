#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.packaging.prepare_kaggle_dataset_folder --folder data/kaggle_uploads/certgen-features --dataset-name certgen-features --source-zip data/results/v6_feature_input.zip
