#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.build_kaggle_feature_input_zip \
  --reference-manifest "${CERTGEN_REFERENCE_MANIFEST:-registry/manifests/cifar10_r1_reference.jsonl}" \
  --generated-manifest "${CERTGEN_GENERATED_MANIFEST:-registry/manifests/cifar10_r1_generated_pilot_1000.jsonl}" \
  --sample-manifest "${CERTGEN_FEATURE_SAMPLE_MANIFEST:-registry/manifests/cifar10_r1_feature_extraction_samples.jsonl}" \
  --provenance-ledger "${CERTGEN_PROVENANCE_LEDGER:-registry/provenance/cifar10_r1_ledger.csv}" \
  --preprocessing-lock "${CERTGEN_PREPROCESSING_LOCK:-configs/preprocessing_locks/cifar10_inception_bilinear_299.json}" \
  --out-zip "${CERTGEN_FEATURE_INPUT_ZIP:-data/kaggle_inputs/certgen_cifar10_feature_extraction_1k_input.zip}" \
  --manifest-out "${CERTGEN_FEATURE_INPUT_MANIFEST:-data/results/v6_feature_input_zip_manifest.json}" \
  --image-policy "${CERTGEN_FEATURE_INPUT_IMAGE_POLICY:-manifest_paths}"
