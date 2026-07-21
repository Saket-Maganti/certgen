#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.validate_cifar10_reference_manifest \
  --manifest "${CERTGEN_REFERENCE_MANIFEST:-registry/manifests/cifar10_r1_reference.jsonl}" \
  --summary-out "${CERTGEN_REFERENCE_VALIDATION_SUMMARY:-data/results/v6_reference_manifest_validation_summary.json}" \
  --expected-count "${CERTGEN_REFERENCE_EXPECTED_COUNT:-10000}"
