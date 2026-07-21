# 09 — Multi-Benchmark Expansion Plan

Implement `CERTGEN_R3_MULTI_BENCHMARK_EXPANSION_PLAN`.

Goal:

> After CIFAR-10 real pilot works, prepare expansion to 3–4 benchmarks without overbuilding.

Do not start new benchmarks until CIFAR-10 has real results and gates pass.

## Candidate benchmarks

Prioritize released samples/features and low friction:

1. CIFAR-10 — current pilot.
2. FFHQ / CelebA-HQ 256 — faces; many generative checkpoints/samples.
3. ImageNet 64/128/256 class-conditional — high relevance but heavier.
4. LSUN category — optional.
5. Video/FVD — stretch only after image core succeeds.

## Tasks

### 1. Build benchmark availability board

Create:

- `registry/multibench/benchmark_availability_r3.csv`
- `docs/R3_MULTI_BENCHMARK_AVAILABILITY_REPORT.md`

Columns:

- benchmark;
- source URL;
- license;
- released real data;
- released generated samples;
- checkpoints;
- sample count;
- feature extraction difficulty;
- expected GPU time;
- metric reproduction feasibility;
- reviewer recognizability;
- status.

### 2. Select next benchmark

Choose the next benchmark based on:

- released samples first;
- clear license;
- reproducible preprocessing;
- reasonable feature extraction time;
- recognizable model comparisons.

### 3. Do not execute heavy runs

This is planning unless CIFAR-10 passes gates.

## Output status

- `READY_FOR_NEXT_BENCHMARK_SELECTION`
- `BLOCKED_WAITING_FOR_CIFAR_RESULTS`
- `BLOCKED_NO_CLEAN_SOURCES`
