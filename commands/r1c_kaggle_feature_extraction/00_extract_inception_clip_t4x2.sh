#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1

WORK_ROOT="${CERTGEN_KAGGLE_WORK_ROOT:-/kaggle/working}"
INPUT_ROOT="${CERTGEN_KAGGLE_INPUT_ROOT:-/kaggle/input/certgen}"
SAMPLE_MANIFEST="${CERTGEN_R1_SAMPLE_MANIFEST:-$INPUT_ROOT/cifar10_r1_feature_extraction_samples.jsonl}"
PROVENANCE_LEDGER="${CERTGEN_R1_PROVENANCE_LEDGER:-$INPUT_ROOT/cifar10_r1_ledger.csv}"
INCEPTION_LOCK="${CERTGEN_R1_INCEPTION_LOCK:-$INPUT_ROOT/cifar10_inception_bilinear_299.json}"
CLIP_LOCK="${CERTGEN_R1_CLIP_LOCK:-$INCEPTION_LOCK}"
FEATURE_ROOT="$WORK_ROOT/features/cifar10_r1"

mkdir -p "$FEATURE_ROOT/inception" "$FEATURE_ROOT/clip" "$FEATURE_ROOT/merged" "$FEATURE_ROOT/split" "$FEATURE_ROOT/logs"

CUDA_VISIBLE_DEVICES=0 python -m certgen.features.extract \
  --input-manifest "$SAMPLE_MANIFEST" \
  --provenance-ledger "$PROVENANCE_LEDGER" \
  --preprocessing-lock "$INCEPTION_LOCK" \
  --extractor inception_v3_pool3 \
  --out-dir "$FEATURE_ROOT/inception" \
  --device cuda \
  --batch-size "${CERTGEN_INCEPTION_BATCH_SIZE:-64}" \
  --shard-id 0 \
  --num-shards 2 \
  --resume \
  --execute > "$FEATURE_ROOT/logs/inception_gpu0.log" 2>&1 &

CUDA_VISIBLE_DEVICES=1 python -m certgen.features.extract \
  --input-manifest "$SAMPLE_MANIFEST" \
  --provenance-ledger "$PROVENANCE_LEDGER" \
  --preprocessing-lock "$INCEPTION_LOCK" \
  --extractor inception_v3_pool3 \
  --out-dir "$FEATURE_ROOT/inception" \
  --device cuda \
  --batch-size "${CERTGEN_INCEPTION_BATCH_SIZE:-64}" \
  --shard-id 1 \
  --num-shards 2 \
  --resume \
  --execute > "$FEATURE_ROOT/logs/inception_gpu1.log" 2>&1 &

wait

CUDA_VISIBLE_DEVICES=0 python -m certgen.features.extract \
  --input-manifest "$SAMPLE_MANIFEST" \
  --provenance-ledger "$PROVENANCE_LEDGER" \
  --preprocessing-lock "$CLIP_LOCK" \
  --extractor clip_vit \
  --out-dir "$FEATURE_ROOT/clip" \
  --device cuda \
  --batch-size "${CERTGEN_CLIP_BATCH_SIZE:-64}" \
  --shard-id 0 \
  --num-shards 2 \
  --resume \
  --execute > "$FEATURE_ROOT/logs/clip_gpu0.log" 2>&1 &

CUDA_VISIBLE_DEVICES=1 python -m certgen.features.extract \
  --input-manifest "$SAMPLE_MANIFEST" \
  --provenance-ledger "$PROVENANCE_LEDGER" \
  --preprocessing-lock "$CLIP_LOCK" \
  --extractor clip_vit \
  --out-dir "$FEATURE_ROOT/clip" \
  --device cuda \
  --batch-size "${CERTGEN_CLIP_BATCH_SIZE:-64}" \
  --shard-id 1 \
  --num-shards 2 \
  --resume \
  --execute > "$FEATURE_ROOT/logs/clip_gpu1.log" 2>&1 &

wait

python -m certgen.features.merge_shards \
  --shard-dir "$FEATURE_ROOT/inception/shard-000-of-002" \
  --shard-dir "$FEATURE_ROOT/inception/shard-001-of-002" \
  --extractor inception_v3_pool3 \
  --out-npz "$FEATURE_ROOT/merged/cifar10_r1_inception.npz" \
  --out-sidecar "$FEATURE_ROOT/merged/cifar10_r1_inception.sidecar.json" \
  --force

python -m certgen.features.merge_shards \
  --shard-dir "$FEATURE_ROOT/clip/shard-000-of-002" \
  --shard-dir "$FEATURE_ROOT/clip/shard-001-of-002" \
  --extractor clip_vit \
  --out-npz "$FEATURE_ROOT/merged/cifar10_r1_clip.npz" \
  --out-sidecar "$FEATURE_ROOT/merged/cifar10_r1_clip.sidecar.json" \
  --force

python -m certgen.features.split_by_role \
  --features-npz "$FEATURE_ROOT/merged/cifar10_r1_inception.npz" \
  --sidecar "$FEATURE_ROOT/merged/cifar10_r1_inception.sidecar.json" \
  --sample-manifest "$SAMPLE_MANIFEST" \
  --extractor-label inception \
  --out-dir "$FEATURE_ROOT/split" \
  --summary-out "$FEATURE_ROOT/split/inception_split_summary.json" \
  --force

python -m certgen.features.split_by_role \
  --features-npz "$FEATURE_ROOT/merged/cifar10_r1_clip.npz" \
  --sidecar "$FEATURE_ROOT/merged/cifar10_r1_clip.sidecar.json" \
  --sample-manifest "$SAMPLE_MANIFEST" \
  --extractor-label clip \
  --out-dir "$FEATURE_ROOT/split" \
  --summary-out "$FEATURE_ROOT/split/clip_split_summary.json" \
  --force
