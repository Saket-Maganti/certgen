# 12 — One-Shot Mega Prompt: CertGen Execution-First Push

You are working on CertGen after V5/R0/R1/R1A/R1B.

Do not build V6 infrastructure. Do not add generic docs, reviewer simulators, scorecards, paper scaffolds, or process-only audits.

Your job is to implement the execution-first mega tranche:

1. fix the remaining technical correctness issues;
2. materialize CIFAR-10 reference samples;
3. prepare and run the Kaggle T4x2 1k/model generation path if real execution is available;
4. validate generated manifests and build a feature-extraction-ready package;
5. prepare/run Kaggle T4x2 Inception+CLIP feature extraction only if the package validates;
6. validate feature caches locally on CPU;
7. reproduce or sanity-check one metric point estimate;
8. run the first CPU clean-core certificate pilot only after gates pass;
9. compute first-benchmark pilot-only undecided fraction;
10. prepare scale-to-10k/50k commands only if gates pass;
11. prepare paper result injection only from eligible real outputs.

Hard boundaries:

- no fake empirical results;
- no paper evidence promotion unless all gates pass;
- no `claim_allowed=true` by default;
- no rigorous FID certificate claim;
- polynomial KID is descriptive/non-certified by default;
- rigorous core uses bounded RBF-MMD and bounded CMMD;
- CPU for all CertGen certificates/reports/audits;
- Kaggle T4x2 only for sample generation and feature extraction.

Current blockers:

- `BLOCKED_MISSING_REFERENCE_SAMPLES`;
- generated samples not run;
- feature extraction blocked;
- certificates blocked.

Start with `01_R0_TECHNICAL_CORRECTION_BETTING_CS_AND_BOUNDED_KERNELS.md`, then continue staged through `11_FINAL_EXECUTION_AUDIT_AND_STOP_RULE.md`.

If any required real source or local path is missing, stop with a precise blocked status and exact next command. Do not replace missing real data with smoke/synthetic data.

Verification after each stage:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
```

Final answer must report:

- tests passed;
- audits passed;
- actual blockers;
- whether Kaggle generation can run;
- whether Kaggle feature extraction can run;
- whether CPU certificate pilot can run;
- real evidence status;
- no fake results / no claim promotion confirmation.
