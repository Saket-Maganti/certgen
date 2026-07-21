#!/usr/bin/env bash
set -euo pipefail
zip_path="${1:?usage: $0 /path/to/certgen_cifar10_generation_outputs.zip}"
python3 -m certgen.packaging.import_kaggle_generation_outputs --zip "$zip_path"
