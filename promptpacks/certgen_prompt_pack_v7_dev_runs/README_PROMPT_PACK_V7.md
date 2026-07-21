# CertGen Prompt Pack V7 — Developmental Run Upgrades + Kaggle Bookruns

This pack is intentionally bigger than V6, but it is not a generic infrastructure pack. It is an execution-development pack.

Current reality before V7:

- V6 CPU/Kaggle bridge exists.
- Tests are reported clean at 157 passed.
- Generation input ZIP exists.
- Final audit remains `BLOCKED_MISSING_REFERENCE_SAMPLES`.
- No real evidence exists.
- No feature extraction, metric reproduction, certificates, or pilot undecided fraction have been run.

V7 goal:

> Make the project harder to stall: add stronger local data onramps, Kaggle notebook bookruns, multi-scale run lanes, output import/recovery, run ledger, failure handling, and scale-ready CPU gates.

Recommended execution order:

1. `00_GLOBAL_RULES_AND_OBJECTIVE.md`
2. `01_LOCAL_DATA_ONRAMP_CIFAR_REFERENCE.md`
3. `02_KAGGLE_BOOKRUN_GENERATION_ORCHESTRATOR.md`
4. `03_KAGGLE_BOOKRUN_FEATURE_EXTRACTION_ORCHESTRATOR.md`
5. `04_CPU_OUTPUT_IMPORT_VALIDATE_RECOVER.md`
6. `05_RUN_LEDGER_AND_STAGE_DASHBOARD.md`
7. `06_MULTI_SCALE_1K_10K_50K_LANES.md`
8. `07_FAILURE_RECOVERY_AND_CHECKPOINT_ADAPTERS.md`
9. `08_METRIC_REPRODUCTION_EXTENSIONS.md`
10. `09_CERTIFICATE_PILOT_EXPANSION_AND_SENSITIVITY.md`
11. `10_MULTI_BENCHMARK_CANDIDATE_ONRAMP.md`
12. `11_KAGGLE_DATASET_PACKAGING_AUTOMATION.md`
13. `12_NOTEBOOK_QUALITY_AND_IDEMPOTENCE.md`
14. `13_PAPER_RESULT_GATE_AND_DRAFT_PLACEHOLDERS.md`
15. `14_DEVOPS_CLEANUP_GIT_ARCHIVE_RELEASE.md`
16. `15_FINAL_V7_AUDIT_AND_HANDOFF.md`

Use `16_ONE_SHOT_MEGA_PROMPT_V7.md` only if you want one large run. Staged execution is safer.

Expected V7 final state:

- CIFAR reference materialization has multiple robust onramps.
- Kaggle generation and feature-extraction notebooks are runnable, resumable, timed, and output zip-safe.
- Local CPU validators can import Kaggle output ZIPs and recover from partial runs.
- 1k/10k/50k lanes are defined with exact escalation gates.
- A run ledger and stage dashboard show exact current blocker.
- No fake evidence or claim promotion occurs.
