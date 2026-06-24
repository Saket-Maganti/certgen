# 04 — V5 Preregistration and Analysis Plan Lock

## Goal

Create a result-free analysis-plan lock so later runs cannot quietly move the target after seeing results.

## Add Files

Create:

- `docs/analysis/PREREGISTRATION_V5.md`
- `docs/analysis/ANALYSIS_PLAN_LOCK_V5.md`
- `data/contracts/analysis_plan_lock_v5.json`
- `certgen/audit/analysis_plan_audit.py`
- `tests/test_v5_analysis_plan_lock.py`

## Required Analysis Plan Sections

1. **Primary question**

   When is one generative model certifiably better than another under a chosen metric, with optional-stopping-safe validity and a sample budget?

2. **Primary pilot endpoint**

   First-benchmark undecided fraction among preselected contestable model pairs.

3. **Primary metrics**

   Clean-core rigorous metrics:

   - KID/MMD-style estimator;
   - CMMD-style CLIP-feature MMD;
   - optionally DINO-feature MMD/FD-style descriptive metrics.

   FID is descriptive/block-experimental unless rigorously resolved.

4. **Primary decision rule**

   Stop when the anytime-valid confidence sequence for `Delta = d(A,R) - d(B,R)` excludes 0, or when the budget is exhausted.

5. **Outcomes**

   - A certified better than B;
   - B certified better than A;
   - not decided at budget;
   - invalid/rejected due to provenance, preprocessing, or metric reproduction failure.

6. **Pilot go/no-go thresholds**

   Use the project thresholds:

   - undecided fraction >= 0.25–0.30: strong go;
   - 0.05–0.25: conditional go;
   - <0.05: weak audit headline, reconsider emphasis.

   These are pilot interpretation thresholds, not paper claims.

7. **Multiple comparisons**

   State whether family-wise or per-comparison alpha applies. Include a conservative default.

8. **Dependence diagnostics**

   Require diagnostic reporting if samples/features are reused across comparisons.

9. **Preprocessing lock**

   State that sample size, resizing, interpolation, crop, color mode, feature extractor, and reference set must be locked before real run.

10. **Exclusions**

   Exclude model pairs with unverifiable sample provenance, unavailable feature caches, license uncertainty, failed metric reproduction, or mismatched preprocessing.

## Lock Hash

Implement a command that computes a hash of the analysis-plan JSON and writes it to:

- `data/results/analysis_plan_lock_hash_v5.txt`

No result injection should proceed unless the current analysis plan hash matches the recorded lock, unless an explicit amendment file exists.

## Amendment Policy

Create:

- `docs/analysis/ANALYSIS_PLAN_AMENDMENT_POLICY.md`

Any post-result analysis-plan changes must be marked:

- `posthoc=true`
- `paper_claim_scope=exploratory`

## Tests

Test that:

- analysis plan exists;
- lock hash is deterministic;
- changing the plan changes the hash;
- result-injection commands fail if lock hash mismatch exists;
- posthoc amendments are clearly marked.
