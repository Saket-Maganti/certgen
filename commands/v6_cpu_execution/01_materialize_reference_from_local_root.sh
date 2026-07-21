#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

: "${CIFAR_ROOT:?Set CIFAR_ROOT to a local CIFAR-10 image tree.}"

commands/r1b_cpu/00_materialize_cifar10_reference_from_local_root.sh
