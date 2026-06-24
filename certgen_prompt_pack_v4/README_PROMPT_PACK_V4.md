# CertGen Prompt Pack V4 — CVPR-Range Upgrade Pack

**Project:** CertGen / Certified Generative-Model Comparison  
**Pack:** V4  
**Purpose:** turn the V1–V3 research scaffold into a CVPR-range empirical machine without weakening evidence boundaries.

V1 established the repo and claim-safe scaffold. V2 added clean-core MMD/KID/CMMD certificate machinery. V3 added real-pilot readiness: provenance ledger, feature-cache contracts, metric reproduction audit, first-pilot orchestrator, deterministic replay, report cards, and no-claim gates.

V4 is the first broad, paper-facing upgrade pack. It should build toward actual empirical execution and CVPR paper readiness, while still refusing to promote any result until real provenance, feature-cache, metric-reproduction, and certificate gates pass.

## What V4 should add

1. Destructive state intake audit over V1–V3.
2. Provenance-to-real-run pipeline.
3. Kaggle/Colab/local feature-extraction notebook generators.
4. Preprocessing locks and metric-reproduction contracts.
5. Advanced certification layer: multiple comparisons, ranking stability, dependence diagnostics, sensitivity.
6. Real first-pilot run controller with go/no-go logic.
7. Audit ingestion for published/reported metric claims.
8. Decidedness and ranking-stability report generators.
9. Paper figures/tables scaffold.
10. CVPR paper skeleton and related-work task board.
11. Reviewer attack harness and response bank.
12. Reproducibility capsule and release safety checks.
13. V4 final audit and handoff.

## Execution style

Run the prompts in order. Do not ask the user before every file. Make conservative implementation choices. Keep heavy imports optional and lazy. Keep tests CPU/local. Do not download datasets or model weights in tests.

Use the one-shot megaprompt only if the implementation agent can handle a long multi-file upgrade safely. Staged execution is preferred.

## Evidence boundary

V4 may create real-run paths, notebooks, registries, and report templates. V4 must not claim:

- a real undecided fraction,
- a real ranking movement,
- a real model win/loss,
- a rigorous FID certificate,
- a paper-ready result,
- or evidence from smoke/synthetic/mock/planned artifacts.

Every generated artifact must carry an evidence status. Smoke and synthetic artifacts must remain `claim_allowed=false`.

## Recommended order

1. `00_V4_GLOBAL_RULES_AND_CVPR_BOUNDARIES.md`
2. `01_V4_STATE_INTAKE_AND_DESTRUCTIVE_AUDIT.md`
3. `02_V4_PROVENANCE_TO_REAL_RUN_PIPELINE.md`
4. `03_V4_FEATURE_EXTRACTION_NOTEBOOK_GENERATORS.md`
5. `04_V4_PREPROCESSING_LOCKS_AND_METRIC_REPRODUCTION.md`
6. `05_V4_ADVANCED_CERTIFICATION_AND_MULTIPLE_COMPARISONS.md`
7. `06_V4_RANKING_STABILITY_AND_DECIDEDNESS_AUDIT.md`
8. `07_V4_FIRST_REAL_PILOT_CONTROLLER_AND_GO_NOGO.md`
9. `08_V4_LITERATURE_AUDIT_INGESTION_AND_CLAIM_TRACE.md`
10. `09_V4_PAPER_FIGURES_TABLES_AND_RESULT_CARDS.md`
11. `10_V4_CVPR_PAPER_SCAFFOLD_AND_RELATED_WORK_BOARD.md`
12. `11_V4_REVIEWER_ATTACK_HARNESS_AND_RESPONSE_BANK.md`
13. `12_V4_REPRODUCIBILITY_CAPSULE_AND_RELEASE_SAFETY.md`
14. `13_V4_FINAL_AUDIT_AND_HANDOFF.md`
15. `14_ONE_SHOT_MEGAPROMPT_V4.md`

## Final V4 success condition

V4 succeeds if the repo can safely progress from:

> “ready to run a pilot if real caches exist”

into:

> “able to validate provenance, validate feature caches, reproduce a metric point estimate, run clean-core certificates over verified real comparisons, generate claim-safe pilot reports, and produce paper-facing figures/tables as non-claim drafts until gates pass.”
