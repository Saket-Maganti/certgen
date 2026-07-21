#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

ARGS=()
if [[ -n "${CIFAR_SEARCH_ROOT:-}" ]]; then
  ARGS+=(--search-root "$CIFAR_SEARCH_ROOT")
fi

python3 -m certgen.data.cifar_reference_super_onramp \
  --explain \
  --out-json data/results/v9_cifar_reference_onramp.json \
  --out-report docs/V9_CIFAR_REFERENCE_SUPER_ONRAMP.md \
  "${ARGS[@]}" \
  "$@"
