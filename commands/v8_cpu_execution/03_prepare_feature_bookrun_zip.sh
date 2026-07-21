#!/usr/bin/env bash
set -euo pipefail
python3 -m certgen.packaging.build_kaggle_feature_input_zip "$@"
