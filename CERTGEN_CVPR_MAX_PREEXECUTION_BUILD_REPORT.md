# CertGen CVPR Maximum Pre-execution Build Report

> **SUPERSEDED — HISTORICAL PRE-EXECUTION SNAPSHOT.** This report predates the final runtime hardening pass. Use `CERTGEN_CVPR_FINAL_RUNTIME_HARDENING_REPORT.md` for current status and evidence.

## 1. Executive verdict

CertGen is now a CVPR-first, claim-safe visual generative-model comparison system built around bounded-RBF pairwise certificates and partial rankings. The local build succeeds conditionally: the 212-test baseline reproduces, the final expanded suite passes 234 tests, the CVPR experiment architecture exists, and no real evidence has been manufactured. Status is `CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT`. The blocker is a missing user-provided CIFAR-10 source. Exact next command: `python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain`.

This moves the repository from a narrow audited core plus V6-V9 scripts to one execution ontology, stage machine, registry suite, hardened notebook factory, certificate/ranking interfaces, figure gates, paper contracts, and a complete run handbook. CVPR merit still depends entirely on real multi-benchmark/model/feature results and visual evidence.

## 2. Reproduced baseline

Baseline: `212 passed`; documented baseline statistical lane `22 passed`; documented baseline artifact lane `18 passed`. Final: `234 passed`, full statistical lane `31/31`, full artifact-contract lane `25/25`, extended CVPR synthetic/gate lane `11/11`, canonical notebooks `5/5`, CVPR audit `8/8`, forensic `8/8`, V9 compatibility audit `22/22`, and final execution audit `BLOCKED_MISSING_REFERENCE_SAMPLES`; compile/import/ruff/paper/privacy/firewall/artifact checks pass. Paper built as a five-page placeholder with box warnings; build byproducts were written outside the repository. Full mypy remains exactly `111 errors in 34 files`, while the new 25-file critical lane passes; this is historical maintenance debt with no incremental errors. The pre-existing dirty worktree and historical prompt-pack deletions were preserved and inventoried in `reports/CERTGEN_CVPR_REPOSITORY_SAFETY_INVENTORY.md`.

## 3. CVPR-readiness gaps found

- Theory: real-run independence/reference/family obligations not yet artifact-enforced by execution.
- Code: no typed CVPR stage/family/ranking/figure layer.
- Architecture: V6-V9 status and wrappers dominated navigation.
- Notebooks: no canonical generic generation/features names; DINO not in the primary extraction contract.
- Breadth: benchmark/model availability and licenses not verified.
- Ranking/visuals: no strict partial-ranking validity gate or paper-approved figure factory.
- Paper/release: working title/claim hierarchy existed but not a unified CVPR contract.

## 4. Repairs implemented

See `reports/CERTGEN_CVPR_REPAIR_CHANGELOG.md` for each finding, severity, root cause, changed files, tests, verification, and remaining limitation. P0 repairs isolate the exact six-kernel bounded contribution, freeze family/reference contracts, enrich the singular next action, require immutable ranking compatibility, and block unapproved empirical rendering. P1 repairs add registries, state machine, canonical notebooks, secure reference wrapper, CLI routes, tests, and runbook. Remaining limits are external data/model/Kaggle and real evidence.

## 5. New systems built

- benchmark, model, feature, comparison, family, claim, preregistration, execution, baseline, ablation, and figure registries/configs;
- 18-state typed machine, stable run IDs/config hashes, atomic output helper, enriched exact next action;
- no-download CIFAR validation/materialization for official/extracted/cache/image/wrapper forms;
- five config-driven process-based T4x2 notebooks and structural analyzer;
- reuse of secure ZIP/import, append-only artifact, and cache-v2 contracts;
- executable metric-reproduction and four-family sanity gates with immutable, nonclaim result schemas;
- configuration-driven runtime/session planner with resource arithmetic and deterministic copyback checkpoints;
- canonical bounded-RBF certificate runner with frozen-family/reference-plan checks;
- partial-ranking graph with unresolved and feature-disagreement outputs;
- censoring-aware samples-to-decision schema and paper-approved figure gates;
- literature claim schema/protocol, runtime/session matrix, paper/reviewer/release contracts;
- self-contained complete run handbook.

## 6. Statistical validity

The implemented contribution is `kAA-kBB-kAR1-kAR2+kBR1+kBR2`, estimating `MMD^2(A,R)-MMD^2(B,R)`. An RBF term is in `[0,1]`; the conservative contribution support is `[-3,3]`. Units use non-overlapping A/B/R pairs; the same R pair within a unit cancels reference-reference terms. A union-Hoeffding CS uses first exclusion of zero; negative certifies A closer and positive B closer. Bonferroni uses the full prospective family. Betting-grid, empirical Bernstein, directional e-BH, FID/FD, and polynomial KID are not certificate-capable. Real independence, fixed choices, source identity, and frozen family remain proof/artifact obligations.

## 7. CVPR experiment program

- Pilot: CIFAR controls and 1k candidate model pairs; execution validation only.
- Minimum credible: two recognized benchmarks, multiple families, three features, controls/baselines/visuals/sensitivity.
- Strong: third/text-to-image domain, material cross-representation and compute consequences, prospective published-claim audit.
- Maximum: broad 50k study and optional video replication only after the image core justifies it.

## 8. Notebook readiness

All five canonical notebooks pass JSON/Python/contract static analysis and have no stored outputs. They implement pinned dependency checks, T4x2 validation, explicit GPU pinning with independent processes, deterministic shards, configuration hashes, atomic statuses, validated resume, partial failure blocking, integrity manifests, deterministic ZIPs, logs, and copyback instructions. They have not run on Kaggle. Packages, auth, checkpoints, runtime adapter, memory, throughput, and model outputs are unverified.

## 9. Verification

The exact baseline and final commands, timestamps, exit codes, durations, counts, warnings, and artifacts are in `reports/CERTGEN_CVPR_COMMAND_LEDGER.csv`. The final audit is `reports/CERTGEN_CVPR_FINAL_AUDIT.json`. No validation command downloads data/models, executes GPU work, or grants paper permission.

## 10. Remaining blockers

- `USER_INPUT_REQUIRED`: provide a local accepted CIFAR source.
- `KAGGLE_EXECUTION_REQUIRED`: checkpoint preflight, generation, and features.
- `REAL_DATA_REQUIRED`: validated references on each benchmark.
- `REAL_MODEL_REQUIRED`: source/license/revision/adapter/preflight per model.
- `REAL_FEATURES_REQUIRED`: immutable Inception/CLIP/DINO caches.
- `EMPIRICAL_RESULT_REQUIRED`: metric, controls, certificates, rankings, sensitivity.
- `PAPER_EVIDENCE_REQUIRED`: multi-benchmark claim gate and visuals.
- `OPTIONAL_POST_PILOT_UPGRADE`: breadth/theory/video only if findings justify.

## 11. CVPR ceiling assessment

Pilot-only execution is not a paper. Workshop level needs a complete single-benchmark result with controls. Minimum CVPR needs breadth, recognizable models, three features, baselines, visual cases, and strong protocol integrity. Competitive CVPR needs a clear practical result across benchmarks. Strong CVPR needs a robust, consequential audit. The maximum realistic ceiling adds broad prospective literature evidence and possibly a separately valid extension; it cannot be inferred before runs.

## 12. Stop-building verdict

`DO NOT BUILD BEFORE FIRST PILOT`: complex e-BH, FID certification, video pipeline, dashboards/web apps, cloud/distributed support, arbitrary metric plugins, migration tooling, new prompt packs.

`ONLY BUILD IF EXECUTION FAILS`: concrete adapter/package/import/cache/resume repairs.

`ONLY BUILD IF RESULTS JUSTIFY IT`: 10k/50k breadth, third benchmark, video.

`POST_PILOT THEORY OPTIONS`: tighter valid CS or dependence design only if power/calibration blocks the registered question.

`POST_PILOT EMPIRICAL EXPANSIONS`: model/benchmark/literature breadth selected prospectively from the pilot interpretation.

## 13. Exact next action

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```
