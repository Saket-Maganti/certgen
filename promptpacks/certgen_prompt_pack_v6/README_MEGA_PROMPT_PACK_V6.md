# CertGen Mega Prompt Pack V6 — Execution-First CVPR Push

This pack is **not** a generic V6 infrastructure pack.

It is a mega execution prompt pack for CertGen after V5/R0/R1/R1A/R1B. It converts the project from
`CVPR-ready-except-runs` into a real empirical study path by forcing the missing pieces:

1. fix the remaining technical correctness issues;
2. materialize CIFAR-10 reference samples;
3. generate 1k/model on Kaggle T4x2;
4. validate/merge manifests;
5. extract Inception + CLIP features on Kaggle T4x2;
6. run metric reproduction locally on CPU;
7. run clean-core certificates locally on CPU;
8. compute the first pilot-only undecided fraction;
9. scale to 10k/50k only after gates pass;
10. prepare paper-ready result injection only from claim-gated real outputs.

## Recommended order

1. `00_GLOBAL_RULES_STOP_INFRASTRUCTURE.md`
2. `01_R0_TECHNICAL_CORRECTION_BETTING_CS_AND_BOUNDED_KERNELS.md`
3. `02_R1B_REFERENCE_MATERIALIZATION_AND_PACKAGE_GATE.md`
4. `03_KAGGLE_T4X2_GENERATION_1K_PER_MODEL.md`
5. `04_CPU_VALIDATE_GENERATED_MANIFESTS_AND_BUILD_PACKAGE.md`
6. `05_KAGGLE_T4X2_FEATURE_EXTRACTION_INCEPTION_CLIP.md`
7. `06_CPU_METRIC_REPRODUCTION_AND_SANITY_GATES.md`
8. `07_CPU_FIRST_CERTIFICATE_PILOT_AND_UNDECIDED_FRACTION.md`
9. `08_SCALE_TO_10K_AND_50K_IF_GATES_PASS.md`
10. `09_MULTI_BENCHMARK_EXPANSION_PLAN.md`
11. `10_CVPR_RESULT_INJECTION_AND_PAPER_POLISH.md`
12. `11_FINAL_EXECUTION_AUDIT_AND_STOP_RULE.md`

Use `12_ONE_SHOT_MEGA_PROMPT_ALL.md` only with a large-context coding agent.

## Core boundary

- CPU: all CertGen validation, metrics from cached features, certificates, reports, audits.
- Kaggle T4x2: only sample generation and feature extraction.
- No fake empirical results.
- No `claim_allowed=true` unless all evidence gates explicitly pass.
- FID remains descriptive-only.
- Polynomial KID remains non-certified by default.
- Rigorous core is bounded RBF-MMD / bounded CMMD.
