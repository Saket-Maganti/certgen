#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

: "${CIFAR_ARCHIVE_ROOT:?Set CIFAR_ARCHIVE_ROOT to a local extracted cifar-10-batches-py directory or parent.}"

commands/r1b_cpu/00b_materialize_cifar10_reference_from_official_archive.sh
