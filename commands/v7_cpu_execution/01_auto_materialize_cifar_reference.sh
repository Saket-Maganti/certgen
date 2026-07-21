#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.data.autodetect_cifar10_root --search-root "${CIFAR_ROOT:-${CIFAR_ARCHIVE_ROOT:-${CIFAR_SEARCH_ROOT:-.}}}" --out-json data/results/v7_cifar_reference_materialization_summary.json --out-report docs/V7_CIFAR_REFERENCE_ONRAMP_REPORT.md
