# CertGen Prompt Pack V2

Purpose: upgrade the V1 CertGen foundation into a technically meaningful clean-core certificate engine while preserving the strict no-claims boundary.

V1 completed:
- 33 tests passing.
- V1 final audit passed, 15/15 checks.
- Config validation, smoke artifacts, registry validation, first-pilot plan generation, and final audit all passed.
- V1 is intentionally conservative: no real feature extraction, no real benchmark audit, no decidedness fraction, no ranking movement claim, and FID/FD-DINOv2 descriptive-only.

V2 target:
- Replace the V1 smoke certificate scaffold with a clean-core KID/MMD/CMMD comparison engine.
- Add anytime-valid confidence sequences/e-processes for bounded comparison streams.
- Add optional-stopping validity simulations.
- Add dry-run-safe first-pilot scaffolding for one verified benchmark path.
- Keep all real empirical claims blocked.

## Recommended order

1. `00_V2_GLOBAL_RULES_AND_BOUNDARIES.md`
2. `01_V2_STATISTICAL_CORE_DESIGN.md`
3. `02_IMPLEMENT_LINEAR_TIME_MMD_STREAMS.md`
4. `03_EMPIRICAL_BERNSTEIN_AND_E_PROCESS_CS.md`
5. `04_OPTIONAL_STOPPING_VALIDITY_LAB.md`
6. `05_CLEAN_METRIC_CERTIFICATE_API.md`
7. `06_CMMD_KID_MMD_INTEGRATION_TESTS.md`
8. `07_FEATURE_CACHE_AND_PREPROCESSING_CONTRACTS.md`
9. `08_DRY_RUN_FIRST_PILOT_PATH.md`
10. `09_REGISTRY_UPGRADES_AND_RELEASED_SAMPLE_AVAILABILITY.md`
11. `10_FID_POLICY_REINFORCEMENT_AND_BLOCK_EXPERIMENT.md`
12. `11_REPORTING_CERTIFICATE_CARDS.md`
13. `12_V2_FINAL_AUDIT_AND_HANDOFF.md`

Use `13_ONE_SHOT_MEGAPROMPT_V2.md` only if you want a single long implementation run.

## V2 success condition

V2 is successful if the repo has a tested clean-core certificate implementation, optional-stopping validity lab, first-pilot dry-run path, and a final V2 audit — with zero real empirical claims promoted.

## V2 failure condition

V2 fails if it claims real results, treats FID as rigorously certified without a valid proof/implementation, runs heavy jobs inside tests, or lets smoke/demo artifacts become paper evidence.
