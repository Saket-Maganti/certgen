# CertGen Prompt Pack V4 Changelog

## V4 purpose

V4 upgrades CertGen from V3 real-pilot readiness into a broader CVPR-range execution and paper-facing infrastructure layer.

## Added prompt files

- `00_V4_GLOBAL_RULES_AND_CVPR_BOUNDARIES.md`
- `01_V4_STATE_INTAKE_AND_DESTRUCTIVE_AUDIT.md`
- `02_V4_PROVENANCE_TO_REAL_RUN_PIPELINE.md`
- `03_V4_FEATURE_EXTRACTION_NOTEBOOK_GENERATORS.md`
- `04_V4_PREPROCESSING_LOCKS_AND_METRIC_REPRODUCTION.md`
- `05_V4_ADVANCED_CERTIFICATION_AND_MULTIPLE_COMPARISONS.md`
- `06_V4_RANKING_STABILITY_AND_DECIDEDNESS_AUDIT.md`
- `07_V4_FIRST_REAL_PILOT_CONTROLLER_AND_GO_NOGO.md`
- `08_V4_LITERATURE_AUDIT_INGESTION_AND_CLAIM_TRACE.md`
- `09_V4_PAPER_FIGURES_TABLES_AND_RESULT_CARDS.md`
- `10_V4_CVPR_PAPER_SCAFFOLD_AND_RELATED_WORK_BOARD.md`
- `11_V4_REVIEWER_ATTACK_HARNESS_AND_RESPONSE_BANK.md`
- `12_V4_REPRODUCIBILITY_CAPSULE_AND_RELEASE_SAFETY.md`
- `13_V4_FINAL_AUDIT_AND_HANDOFF.md`
- `14_ONE_SHOT_MEGAPROMPT_V4.md`
- `CERTGEN_PROJECT_MASTER_CONTEXT_V4_ADDENDUM.md`

## Main upgrades over V3

- Broader real-run pipeline.
- Feature extraction notebook generation.
- Stronger preprocessing lock and metric reproduction gates.
- Batch certificate and multiple-comparison infrastructure.
- Ranking-stability and decidedness analysis.
- First real pilot go/no-go controller.
- Literature claim ingestion and trace.
- Paper artifact scaffolding.
- CVPR paper skeleton.
- Reviewer attack harness.
- Reproducibility capsule and release scan.
- 25+ check final audit.

## Evidence boundary retained

V4 must not create real empirical claims unless real gates pass. In normal V4 implementation, all generated artifacts should remain non-claim unless the user separately supplies verified real data and runs the real pilot.

## Next after V4

V5 should not be another broad infrastructure pack by default. V5 should be real-run execution:

1. fill one real provenance ledger,
2. acquire or validate real feature caches,
3. reproduce one metric point estimate,
4. run first clean-core pilot,
5. measure first-benchmark undecided fraction,
6. decide GO/NO-GO.
