# CertGen Prompt Pack V3 — Real-Pilot Readiness + Heavy Infrastructure Polish

## Purpose

This V3 pack upgrades CertGen from a V2 smoke-valid statistical scaffold into a **real-pilot-ready, provenance-hardened, feature-cache-aware, audit-driven research codebase**.

V1 established the foundation.  
V2 implemented the clean-core MMD/KID/CMMD streams, bounded CS scaffold, certificate API, optional-stopping smoke lab, registry validators, FID policy reinforcement, and certificate-card reporting.

V3 should now do the next useful thing:

> prepare CertGen to run the first real clean-core pilot on one verified public/free benchmark and a small set of released sample/model pairs, without allowing any empirical claim until provenance, feature-cache, metric, and certificate gates pass.

## What V3 should build

V3 should add:

1. A project-state intake audit that verifies V1/V2 state before changing code.
2. A released-sample provenance ledger.
3. A real-feature-cache contract and validator that can reject stale, mismatched, incomplete, or non-reproducible feature caches.
4. Dry-run-safe feature extraction adapters and command plans.
5. Preprocessing and metric-reproduction audits.
6. First-benchmark clean-core pilot orchestration.
7. Certificate replay and determinism checks.
8. Pilot report cards and no-claim gates.
9. Stronger registry schema and sample-availability tables.
10. A V3 final audit and single-file handoff.

## What V3 must not do

V3 must not:

- fabricate benchmark rows;
- fabricate samples, scores, features, or citations;
- declare a decidedness fraction unless real validated feature caches exist;
- claim a model win;
- claim a ranking change;
- claim a published result is wrong;
- turn smoke/synthetic fixtures into evidence;
- implement a rigorous FID certificate unless the FID nonlinear/bias problem is actually solved;
- run heavy downloads automatically inside tests;
- require paid resources or paid APIs.

## Recommended execution

Use staged prompts in order:

1. `00_V3_GLOBAL_RULES_AND_BOUNDARIES.md`
2. `01_V3_PROJECT_STATE_INTAKE_AUDIT.md`
3. `02_V3_RELEASED_SAMPLE_PROVENANCE_LEDGER.md`
4. `03_V3_REAL_FEATURE_CACHE_CONTRACTS.md`
5. `04_V3_DRY_RUN_FEATURE_EXTRACTION_ADAPTERS.md`
6. `05_V3_PREPROCESSING_AND_METRIC_REPRODUCTION_AUDIT.md`
7. `06_V3_FIRST_BENCHMARK_PILOT_ORCHESTRATOR.md`
8. `07_V3_CERTIFICATE_REPLAY_AND_DETERMINISM.md`
9. `08_V3_PILOT_REPORT_CARDS_AND_NO_CLAIM_GATES.md`
10. `09_V3_REGISTRY_SCHEMA_AND_AVAILABILITY_TABLES.md`
11. `10_V3_OPTIONAL_STOPPING_LAB_UPGRADE.md`
12. `11_V3_DOCS_COMMANDS_AND_REPRODUCIBILITY_POLISH.md`
13. `12_V3_FINAL_AUDIT_AND_HANDOFF.md`

Use `13_ONE_SHOT_MEGAPROMPT_V3.md` only if you deliberately want a single long implementation run. Staged execution is safer.

## Expected V3 outcome

At the end of V3, the repo should be able to:

- verify whether a candidate real benchmark/model-pair row is usable;
- validate feature caches against strict metadata and hash contracts;
- run a dry-run-safe first-pilot plan;
- run clean-core certificates on validated real features only when present;
- render no-claim pilot cards;
- report a first-benchmark undecided fraction **only if** all real evidence gates pass;
- otherwise honestly report `NO_REAL_EVIDENCE` or `REAL_FEATURES_NOT_VALIDATED`.

## V3 success definition

A successful V3 final audit should pass checks covering:

- V1/V2 state compatibility;
- clean-core metric/certificate availability;
- registry and provenance validation;
- feature-cache schema validation;
- dry-run first-pilot command generation;
- metric reproduction audit scaffolding;
- certificate replay determinism;
- claim gates;
- FID descriptive-only policy;
- report-card generation;
- command index;
- reproducibility docs;
- final handoff.

## V3 guiding sentence

CertGen V3 is not about getting a result. It is about making the first real result impossible to fake, impossible to overclaim, and easy to reproduce.
