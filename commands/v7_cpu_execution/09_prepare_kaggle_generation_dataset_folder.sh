#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.packaging.prepare_kaggle_dataset_folder --folder data/kaggle_uploads/certgen-generation --dataset-name certgen-generation --source-zip "${GENERATION_INPUT_ZIP:-}"
