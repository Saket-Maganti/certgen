# CertGen Evidence-Boundary Audit

Verdict: `NO_CLAIM_CAPABLE_EMPIRICAL_EVIDENCE`. `claim_allowed=false`.

## Scope and method

The audit inspected live JSON/JSONL/CSV result files, Markdown and LaTeX claims, notebook source/output state, NPZ/ZIP artifacts, manifests, certificate/replay outputs, paper placeholders, and claim-gate code. It searched the repository for result language including `claim_allowed`, certificate/winner terms, undecided fraction, samples-to-decision, FID/KID/MMD/CMMD, optional stopping, e-values, and e-BH.

At final-document drafting time the tree contained 142 JSON, 8 JSONL, 26 CSV, 361 Markdown, 23 LaTeX, 10 notebook, 32 NPZ, and one ZIP file. Counts are inventory facts, not research evidence, and may increase when final reports are regenerated.

## Artifact verdict

| Surface | Live finding | Classification | Paper permission |
|---|---|---|---|
| CIFAR reference manifests | reference and generated manifests contain zero rows; six-row planning manifest points to missing files | `MISSING` / `PLANNING_ONLY` | no |
| NPZ arrays | all 32 are under smoke fixture directories | `SYNTHETIC_ONLY` | no |
| Generation ZIP | SHA-256 `20ef989fb8f1e54aa7013c143926c79e535948a23b30f341229cfa8678cba8db`; code/config package, no images | `PLANNING_ONLY` and stale after repairs | no |
| Checkpoint preflight | metadata and notebook only; no copied-back successful run | `MISSING` | no |
| Generated samples | no validated archive or nonempty manifest | `MISSING` | no |
| Real features | no real Inception/CLIP/DINOv2 cache | `MISSING` | no |
| Metric reproduction | smoke/internal statuses only; no trusted hash-bound real agreement | `MISSING` | no |
| Sanity controls | plans only | `MISSING` | no |
| Certificates | fixtures, smoke outputs, and replays only | `SYNTHETIC_ONLY` | no |
| Undecided fraction / stopping curve | status placeholders only | `MISSING` | no |
| Paper results | explicit placeholders, no approved cell | `MISSING` | no |

No parsed JSON/JSONL artifact under `data/`, `reports/`, or `release/` currently contains an affirmative `claim_allowed` boolean. Text examples of the field do not constitute promotion.

## Repaired boundary defects

1. Smoke V3 certificates and replay outputs that called themselves `real_pilot_non_claim` were relabeled synthetic/non-evidence.
2. Smoke metric-reproduction outputs that called themselves `real_features_validated` are now classified from their actual input paths and sidecars.
3. The paper firewall now evaluates forbidden result language at claim-line scope; a safe placeholder elsewhere in the file no longer suppresses a real-looking sentence.
4. The manuscript's claim that real benchmarks had been answered was removed.
5. The finite-grid betting and empirical-Bernstein paths cannot issue a directional certificate; e-BH output says point-null rather than directional.
6. Real-like certificates require a reference draw plan, canonical cache-v2 validation, exact feature hashes, a metric specification hash, and a qualifying reproduction class.
7. Imported archives remain `claim_allowed=false`, receive immutable hashes/run IDs, and enter an append-only registry only after local validation.

Regression coverage is in `tests/test_engineering_evidence_safety.py`, `tests/test_feature_cache_v2_contract.py`, `tests/test_reference_draw_plan.py`, and the statistical certificate tests.

## Firewall rule

The paper may discuss verified implementation and conditional theory in present tense. Any dataset/model outcome, winner, measured fraction, sample-to-decision, runtime, ranking, or benchmark generalization requires an approved same-lineage row in the claim-evidence ledger and a separate passing paper injection gate. No row currently has permission.

## Remaining evidence blockers

The immediate blocker is a validated local CIFAR-10 reference source. Later stages require real checkpoint preflight, generation, safe import, feature cache-v2 validation, metric reproduction, real controls, a frozen Bonferroni family, certificate trajectories, censored aggregation, and paper approval. Passing software tests cannot substitute for any of these stages.
