# 00 — Global Rules: Stop Infrastructure, Execute the Empirical Path

You are working on CertGen after V5, R0, R1, R1A, and R1B.

Do **not** create V6 infrastructure.
Do **not** add generic reviewer simulators, readiness scorecards, handoff docs, paper scaffolds, prompt-pack metadata, or process-only audits unless directly required by the execution path.

## Current known state

- V5: CVPR-ready-except-runs scaffold implemented.
- R0: CPU/GPU split implemented. CertGen certificates/reports/audits are CPU-default. Kaggle T4x2 is only for feature extraction and optional sample generation.
- R1: source selection/provenance lock implemented.
- R1A: sample materialization prep implemented.
- R1B: reference/generation package path implemented.
- Tests at last status: 148 passed.
- R1 status: `BLOCKED_MISSING_REFERENCE_SAMPLES`.
- Generated sample package: `BLOCKED_GENERATION_NOT_RUN`.
- Kaggle 1k generation command exists.
- Kaggle feature extraction is not ready yet.
- No real empirical results exist.
- No paper evidence exists.
- No `claim_allowed=true` artifacts should exist.

## External audit verdict to obey

The external audit said:

- the project is overbuilt relative to the lack of real evidence;
- current CVPR readiness is low until real runs exist;
- do not build more infrastructure;
- fix technical correctness issues;
- run CIFAR-10 pilot;
- compute the first real pilot-only undecided fraction;
- consider CVPR vs NeurIPS/ICML after evidence, not before.

## Hard boundaries

1. Do not fabricate results.
2. Do not promote smoke/template/pilot artifacts to paper evidence.
3. Do not create `claim_allowed=true` unless every real evidence gate passes and the task explicitly permits it.
4. FID and FD-style metrics remain descriptive-only.
5. Polynomial KID is not the rigorous certified core unless separately justified.
6. Rigorous certificate core uses bounded RBF-MMD and bounded CMMD.
7. CPU-default for CertGen runs:
   - provenance validation
   - feature-cache validation
   - metric reproduction from cached features
   - certificates
   - optional-stopping lab
   - block-size sensitivity
   - reports
   - audits
8. Kaggle T4x2 only for:
   - sample generation
   - Inception/CLIP/DINO feature extraction
9. Start small:
   - 1,000 generated samples/model first;
   - then 10,000/model;
   - then 50,000/model only after gates pass.

## Final objective

Produce a real, claim-gated, pilot-only CIFAR-10 run path that can answer:

> On the first real benchmark, what fraction of selected model-pair comparisons are statistically undecided under the clean-core certificate?

If real sources or execution fail, stop with a precise blocked status and replacement candidates.
