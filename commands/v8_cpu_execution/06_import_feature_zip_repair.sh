#!/usr/bin/env bash
set -euo pipefail
zip_path="${1:?usage: $0 /path/to/certgen_cifar10_features_outputs.zip}"
python3 -m certgen.packaging.import_kaggle_feature_outputs --zip "$zip_path"
