# CERTVIC — FINAL RUN-READINESS PATCH, PORTABLE EXECUTION, AND SCIENTIFIC GATE CLOSURE MASTER PROMPT

## Role

You are operating as the lead research engineer, benchmark architect, VLM deployment engineer, Kaggle runtime engineer, human-evaluation systems designer, statistician, reproducibility engineer, release engineer, and critical CVPR co-author for **CertVIC**.

This is the final implementation pass before real Kaggle smoke and scientific execution.

Do not perform another broad audit.

Do not create another optimistic scaffold.

Do not stop after documenting gaps.

Your job is to repair every remaining local integration defect, validate the full end-to-end synthetic routes, and leave the repository ready for real Kaggle smoke followed by the independent confirmatory study.

The target status is:

```text
CVPR_PRE_EXECUTION_READY
```

You may use that status only when all local defects described below are fixed and the only remaining blockers are external:

- wheelhouse bytes;
- model snapshots;
- real Kaggle smoke;
- source datasets;
- real human review;
- and real scientific runs.

If any local defect remains, report:

```text
PARTIALLY_READY_WITH_BLOCKERS
```

and name the exact failing path.

---

# 1. Repository

```text
/Users/saketmaganti/Projects/certVIC
```

Treat the live repository as the source of truth.

Preserve:

- historical provider outputs;
- original image pairs;
- canonical manifests;
- review originals;
- evidence and gate ledgers;
- user-owned files;
- and all scientific provenance.

Do not initialize Git when absent.

Do not commit or push unless explicitly requested.

---

# 2. Frozen scientific boundaries

These facts must remain unchanged unless direct repository evidence proves otherwise:

- Qwen2.5-VL-7B has `12/94 = 0.1277` V1 irrelevant-edit flips.
- InternVL2-8B has `1/94 = 0.0106`.
- LLaVA-OneVision-7B has `3/94 = 0.0319`.
- The frozen V1 rule remains:

```text
observed_spurious_flip_rate <= 0.10
```

- Qwen fails the frozen V1 rule.
- The current V2-30 set is retrospective sensitivity evidence only.
- The independent confirmatory study must remain prospective and zero-overlap with V1.
- Main execution remains blocked until confirmatory and review gates pass.
- No real second-domain evidence exists.
- `paper_evidence=false`.
- `human_reviewed=true` count remains zero until genuine review exists.
- No result-oriented threshold, prompt, item, expected-answer, or model-revision tuning is permitted.

---

# 3. Confirmed remaining defects

Verify each defect in the live repository and repair every confirmed issue.

## 3.1 Scientific task paths are not portable

Canonical tasks currently risk binding machine-specific absolute paths such as:

```text
/Users/.../ADE20K/...
```

which will not resolve on Kaggle.

Task hashes must not depend on host-specific absolute paths.

## 3.2 Notebook authorization is not bound to current inputs before GPU work

Scientific notebooks may verify only the permission artifact’s signature, not whether it matches the currently mounted:

- task bundle;
- review artifact;
- freeze manifest;
- smoke gate;
- model registry;
- environment lock;
- code bundle;
- and current hashes.

This can waste GPU time on an unauthorized configuration.

## 3.3 One-run permissions are replayable

Permissions are described as one-run but can currently be verified multiple times.

There is no consumption ledger or state transition.

## 3.4 Synthetic closure does not use the strict smoke validator end to end

The synthetic routes may inject hand-built PASS smoke artifacts instead of constructing realistic smoke ZIPs and passing them through:

```text
smoke_contract
→ smoke_gate
→ execution_gate
```

## 3.5 Confirmatory synthetic route stops before model import and analysis

The synthetic confirmatory route must continue through:

- three mock provider runs;
- strict output packaging;
- atomic import;
- specificity analysis;
- evidence/gate update;
- confirmatory outcome;
- and Main go/no-go.

## 3.6 COCO synthetic route stops at task construction

The COCO synthetic route must include:

- synthetic generation;
- QA;
- review;
- selection;
- three-provider mock execution;
- import;
- feasibility analysis;
- and expansion decision.

## 3.7 Confirmatory set-level detectability gate is not implemented

The prospective config declares:

```text
set_level_symmetric_detectability_auc_max: 0.80
```

but the final selected set is not currently evaluated against that gate.

## 3.8 Main finalization remains greedy

Main selection may report shortages even when a feasible assignment exists.

It also does not fully enforce the declared study strata.

## 3.9 Main “locked strata” are not machine-specified

The config lists stratum names but does not define exact targets, ranges, or tolerances.

## 3.10 Confirmatory exact solver has no deterministic fallback

The solver fails closed on resource limits but does not provide the planned ILP/min-cost-flow fallback.

---

# 4. Primary mission

By the end of this task:

1. All scientific tasks must use portable bundle-relative paths.
2. Every notebook must bind execution permission to the currently mounted inputs before model loading.
3. One-run permissions must be consumable and replay-protected.
4. The synthetic closure must use the real smoke contract and strict smoke gate.
5. The confirmatory synthetic route must complete model execution, atomic import, and analysis.
6. The COCO synthetic route must complete its full feasibility chain.
7. The set-level detectability gate must be implemented and enforced.
8. Main final selection must use an exact solver.
9. Main stratum targets must be explicitly frozen.
10. Confirmatory solving must have a deterministic fallback or explicit resource-limit handling.
11. The full release must contain and validate all new paths.
12. The next action after completion must be real Kaggle smoke, not another repair prompt.

---

# 5. Restrictions

## 5.1 No real scientific execution

Do not run:

- real VLM inference;
- real Main or COCO inference;
- real human review;
- full diffusion generation;
- large model downloads;
- large dataset downloads;
- paid APIs.

Synthetic and non-evidence fixtures are allowed.

## 5.2 No fabricated evidence

Do not fabricate:

- predictions;
- human labels;
- metrics;
- model commits;
- paper results;
- or measured runtimes.

## 5.3 No result-oriented tuning

Do not alter scientific rules after seeing outcomes.

## 5.4 Build, do not merely document

Every confirmed defect must result in:

- code;
- tests;
- a validated CLI;
- notebook changes;
- or a precise external blocker.

---

# PHASE 0 — Reproduce the baseline

Run and record:

- full test suite;
- absolute-final tests;
- notebook tests;
- smoke tests;
- authorization tests;
- Main tests;
- COCO tests;
- claim guard;
- privacy guard;
- paper compile;
- release extraction;
- deterministic release rebuild.

Create:

```text
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_SESSION.md
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_DEFECTS.csv
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_CHANGELOG.csv
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_COMMANDS.csv
```

---

# PHASE 1 — Portable scientific task bundles

Create or update:

```text
certvic/cvpr/task_bundle.py
```

## 1.1 Logical paths

Store only bundle-relative paths such as:

```text
images/source/<ID>.png
images/edited/<ID>.png
masks/<ID>.png
assets/<ID>.png
```

Do not store host-specific absolute paths in the canonical task hash.

## 1.2 Bundle root

Each runtime must accept:

```text
--bundle-root
```

or an equivalent verified configuration.

Resolve logical paths only after verifying the bundle.

## 1.3 Task hash

Bind tasks to:

- logical relative path;
- file-byte hash;
- file size;
- canonical metadata;
- bundle manifest hash;
- schema version.

## 1.4 Bundle manifest

Create:

```text
task_bundle_manifest.json
```

containing:

- every relative file;
- size;
- SHA-256;
- role;
- task IDs;
- study;
- schema;
- bundle hash.

## 1.5 Rebase support

Provide:

```bash
python3 -m certvic.cvpr.task_bundle verify \
  --bundle-root <ROOT> \
  --manifest <MANIFEST>
```

No task hash may change merely because the bundle root changes.

## 1.6 Migration

Provide an explicit converter for existing local absolute-path synthetic fixtures.

## 1.7 Tests

Prove that the same bundle validates under:

```text
/tmp/local_bundle
/kaggle/input/certvic_bundle
```

with identical task and bundle hashes.

---

# PHASE 2 — Bind permission to current notebook inputs

Update every scientific notebook and the worker.

## 2.1 Required current inputs

Before model loading, verify the permission against:

- task bundle manifest;
- final task freeze;
- final review ledger;
- smoke gate;
- environment lock;
- model registry;
- model snapshot manifest;
- code bundle hash;
- study config;
- schema version;
- provider;
- run tag.

## 2.2 Notebook verification

Scientific notebooks must call:

```python
verify_permission(
    permission_path,
    study=...,
    input_paths=current_input_map,
    expected_code_hash=current_code_hash,
    expected_provider=...,
    expected_run_tag=...,
)
```

or an equivalent strict interface.

## 2.3 Fail before model loading

Any mismatch must stop execution before:

- model initialization;
- CUDA allocation;
- or output directory creation.

## 2.4 Tests

Add notebook-runtime tests proving mismatched current inputs fail before the mock adapter is prepared.

---

# PHASE 3 — One-run permission consumption

Create:

```text
certvic/cvpr/permission_ledger.py
```

## 3.1 States

Use:

```text
ISSUED
CLAIMED
RUN_STARTED
OUTPUT_PACKAGED
IMPORTED
CONSUMED
REVOKED
EXPIRED
FAILED
```

## 3.2 Claim

A permission must be atomically claimed for:

- study;
- provider;
- run tag;
- notebook;
- and task universe.

## 3.3 Replay prevention

A consumed or already-claimed permission must fail for an incompatible second run.

## 3.4 Matrix semantics

For a three-provider study, either:

- issue one provider-specific permission per model;
- or one matrix permission with three atomic provider slots.

Choose one clear design.

## 3.5 Transitions

The worker, packager, and importer must update the ledger.

## 3.6 Recovery

Support:

- failed run release;
- explicit authorized retry;
- and revocation.

Do not silently reuse a failed permission.

## 3.7 Tests

Prove:

- second claim fails;
- consumed replay fails;
- wrong provider fails;
- wrong run tag fails;
- valid retry requires a new authorization artifact.

---

# PHASE 4 — Strict smoke in the synthetic closure

The synthetic proof must create realistic smoke packages.

## 4.1 Build trusted two-item smoke fixtures

For each provider create:

- exact two-item task bundle;
- expected model contract;
- expected prompt hash;
- expected parser version;
- expected image hashes;
- expected task hashes;
- expected run-contract hash.

## 4.2 Build synthetic smoke ZIPs

Use the same packaging code as real 00C2.

## 4.3 Validate through the real gate

Pass the ZIPs through:

```text
smoke_contract.py
smoke_gate.py
```

Do not inject hand-written PASS artifacts.

## 4.4 Authorization

Feed only the real smoke-gate output into `execution_gate.py`.

## 4.5 Negative tests

Tamper with:

- one image hash;
- one task hash;
- model ID;
- revision;
- snapshot hash;
- prompt hash;
- ZIP member hash.

Every tampered package must fail.

---

# PHASE 5 — Complete synthetic confirmatory execution

Extend the synthetic confirmatory route through:

1. final selected task bundle;
2. strict smoke validation;
3. signed provider permissions;
4. three mock provider runs;
5. strict run packaging;
6. matrix-complete atomic import;
7. raw specificity analysis;
8. human-filtered analysis;
9. Bonferroni decision;
10. McNemar/Holm comparisons;
11. evidence-ledger update;
12. gate-ledger update;
13. confirmatory outcome artifact;
14. Main go/no-go artifact.

Label all outputs:

```text
SYNTHETIC_END_TO_END_FIXTURE
paper_evidence=false
human_reviewed=false
```

Add assertions that no synthetic artifact enters real evidence directories.

---

# PHASE 6 — Complete synthetic COCO feasibility

Extend the COCO synthetic route through:

1. COCO-60 task bundle;
2. synthetic removal and insertion generation;
3. QA;
4. visual review packet;
5. synthetic review and adjudication;
6. exact selection;
7. task freeze;
8. smoke authorization;
9. three mock provider runs;
10. atomic import;
11. feasibility analysis;
12. expansion decision.

The output must clearly state:

```text
SYNTHETIC_COCO_FEASIBILITY_COMPLETE
paper_evidence=false
```

---

# PHASE 7 — Set-level detectability gate

Create:

```text
certvic/cvpr/detectability_gate.py
```

## 7.1 Inputs

Use the final selected confirmatory task bundle before provider execution.

## 7.2 Grouping

Group by source image or source family to prevent leakage.

## 7.3 Metric

Compute symmetric detectability AUC:

```text
max(AUC, 1 - AUC)
```

using a reproducible CPU-safe classifier or the project’s validated method.

## 7.4 Uncertainty

Provide:

- grouped bootstrap interval;
- fold-level results;
- perturbation-family results;
- and overall result.

## 7.5 Decision

Enforce:

```text
symmetric_detectability_auc <= 0.80
```

or the frozen prospective threshold.

## 7.6 Timing

This gate must run:

- after final selection;
- before provider outputs;
- and before execution authorization.

## 7.7 Fail behavior

If the set fails, produce:

```text
DETECTABILITY_GATE_FAIL
```

and require prospective reconstruction.

Do not remove items after seeing provider outputs.

---

# PHASE 8 — Exact Main finalization

Replace greedy Main selection with the shared exact solver framework.

## 8.1 Freeze Main design targets

Update:

```text
configs/studies/main_study_cvpr.yaml
```

with explicit targets or tolerances for:

- edit family;
- category;
- answer transition;
- target size;
- target position;
- image complexity;
- difficulty;
- engine family;
- source diversity;
- question template;
- edit magnitude.

## 8.2 Exact selection

Use:

- exact in-repo solver;
- memoization;
- pruning;
- timeout;
- deterministic ordering;
- optional ILP/min-cost-flow fallback.

## 8.3 Primary/reserve assignment

Solve both jointly rather than greedily.

## 8.4 Same-stratum replacement

Define the exact stratum key used for replacements.

## 8.5 Proof artifact

Produce:

```text
main_solver_report.json
```

with:

- constraints;
- achieved counts;
- feasibility;
- objective;
- states explored;
- runtime;
- fallback used;
- freeze hash.

## 8.6 Regression test

Include a case where greedy selection fails but exact selection succeeds.

---

# PHASE 9 — Confirmatory solver fallback

## 9.1 Resource limits

Keep:

- max states;
- timeout;
- progress reporting.

## 9.2 Optional backend

Implement an optional deterministic backend using one of:

- SciPy MILP;
- PuLP;
- OR-Tools;
- min-cost flow.

Use only when available and pinned.

## 9.3 Clear statuses

Distinguish:

```text
FEASIBLE_SELECTION_FOUND
NO_FEASIBLE_SELECTION_EXISTS
SOLVER_RESOURCE_LIMIT
OPTIONAL_SOLVER_UNAVAILABLE
```

## 9.4 Determinism

The same inputs and environment must produce the same solution.

---

# PHASE 10 — Update execution authorization order

The execution authorization must require:

- strict smoke PASS for all required models;
- portable task bundle verified;
- review finalized;
- selection solved;
- task freeze signed;
- detectability gate passed;
- environment locked;
- model snapshots locked;
- code hash locked;
- permission ledger initialized.

The notebook must not start without all of these.

---

# PHASE 11 — Update all notebooks

Repair all 16 CVPR notebooks.

Every scientific notebook must:

- use portable bundle-relative task paths;
- verify task bundle manifest;
- verify current permission inputs;
- atomically claim its permission;
- verify schema;
- verify smoke gate;
- verify environment;
- verify snapshots;
- fail before model loading on mismatch;
- update permission state;
- package outputs strictly;
- print exact import instructions.

Generation notebooks must also:

- use strict generation packaging;
- verify detectability-gate prerequisites where applicable;
- support single-GPU fallback;
- preserve portable output bundles.

---

# PHASE 12 — Update post-run import

The importer must:

- verify the consumed/active permission state;
- verify provider slot;
- verify run tag;
- verify task bundle;
- verify task freeze;
- verify current code/environment/model contracts;
- atomically promote all providers;
- transition permission state to `IMPORTED` and then `CONSUMED`;
- reject replayed outputs.

---

# PHASE 13 — Release and clean extraction

Update the self-contained release to include:

- task-bundle tools;
- permission ledger;
- strict smoke fixtures;
- detectability gate;
- exact Main solver;
- synthetic confirmatory route;
- synthetic COCO route;
- updated notebooks;
- updated guides;
- updated execution plan.

From a clean extraction, run:

- task bundle verify;
- synthetic smoke build;
- strict smoke gate;
- execution authorization;
- permission claim;
- mock worker;
- strict package;
- atomic import;
- detectability gate;
- Main exact selection;
- synthetic confirmatory closure;
- synthetic COCO closure.

Rebuild twice and require byte identity.

---

# PHASE 14 — Update the execution master plan

Update:

```text
CERTVIC_CVPR_EXECUTION_MASTER_PLAN.md
docs/execution/CERTVIC_CVPR_EXECUTION_MASTER_PLAN.md
```

The next real route must be:

1. provision wheelhouse;
2. provision model snapshots;
3. create portable two-item smoke bundle;
4. run 00A;
5. run 00B;
6. run 00C2 for all three models;
7. validate strict smoke gate;
8. provision source data;
9. build portable confirmatory candidate bundle;
10. generate controls;
11. run QA;
12. complete human review;
13. exact selection;
14. detectability gate;
15. freeze tasks;
16. authorize execution;
17. run three models;
18. atomically import;
19. analyze;
20. evaluate Main go/no-go.

For every run include:

- exact input;
- command or notebook;
- hardware;
- expected runtime;
- output;
- validation;
- resume;
- failure recovery;
- downstream gate.

---

# PHASE 15 — Potential high-value upgrades

Implement only where they improve correctness.

## 15.1 Permission audit timeline

Create a complete timeline from authorization to consumption.

## 15.2 Bundle diff tool

Compare two task bundles and explain whether reauthorization is required.

## 15.3 Reproducibility capsule

Create one machine-readable artifact containing:

- task bundle hash;
- code hash;
- environment hash;
- snapshot hashes;
- review hash;
- detectability result;
- permission hash.

## 15.4 Failure replay

Reconstruct any failed item using only the portable bundle and run contract.

## 15.5 Smoke-derived runtime calibration

Consume real smoke manifests later and update runtime estimates.

---

# PHASE 16 — Required deliverables

Create or update:

```text
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_SESSION.md
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_DEFECTS.csv
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_CHANGELOG.csv
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_COMMANDS.csv
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_VALIDATION.md
reports/cvpr_run_readiness/CERTVIC_RUN_READINESS_SCORECARD.md
reports/cvpr_run_readiness/CERTVIC_READY_TO_RUN_HANDOFF.md

certvic/cvpr/task_bundle.py
certvic/cvpr/permission_ledger.py
certvic/cvpr/detectability_gate.py

docs/execution/CERTVIC_PORTABLE_TASK_BUNDLE_GUIDE.md
docs/execution/CERTVIC_PERMISSION_CONSUMPTION_GUIDE.md
docs/execution/CERTVIC_DETECTABILITY_GATE_GUIDE.md
docs/execution/CERTVIC_MAIN_EXACT_SELECTION_GUIDE.md
docs/execution/CERTVIC_REAL_RUN_AUTHORIZATION_GUIDE.md

CERTVIC_CVPR_EXECUTION_MASTER_PLAN.md
```

---

# PHASE 17 — Final validation

Run:

- focused run-readiness tests;
- full test suite;
- Ruff;
- compileall;
- type checks when configured;
- portable path tests;
- task-bundle rebase tests;
- permission-input binding tests;
- permission replay tests;
- strict synthetic smoke tests;
- confirmatory full synthetic execution;
- COCO full synthetic feasibility execution;
- detectability-gate tests;
- Main exact-selection tests;
- solver fallback tests;
- notebook static tests;
- notebook synthetic-runtime tests;
- claim guard;
- privacy guard;
- paper compile;
- clean release extraction;
- deterministic release rebuild;
- `git diff --check` when applicable.

Verify explicitly:

```text
paper_evidence=false
human_reviewed=true count = 0 unless genuine review exists
Main execution_allowed=false
COCO execution_allowed=false
V2-30 remains retrospective
no real GPU evidence created
no human labels fabricated
task hashes are independent of host absolute paths
scientific notebooks verify current permission inputs before model loading
one-run permissions cannot be replayed
synthetic closure uses the real smoke gate
confirmatory synthetic route completes import and analysis
COCO synthetic route completes feasibility analysis
detectability gate is enforced before execution authorization
Main selection is exact and respects frozen strata
release works from clean extraction
```

---

# 6. Final status rule

Report:

```text
CVPR_PRE_EXECUTION_READY
```

only when all local defects are closed and the complete synthetic routes pass.

Otherwise report:

```text
PARTIALLY_READY_WITH_BLOCKERS
```

and list the exact remaining local defect.

---

# 7. Required final response

Use this structure:

## 1. Executive verdict

## 2. Final defects repaired

For each include:

- path;
- defect;
- repair;
- test;
- result.

## 3. Portable task bundles

## 4. Strict permission binding and consumption

## 5. Real smoke proof

## 6. Confirmatory full synthetic route

## 7. COCO full synthetic route

## 8. Detectability gate

## 9. Main exact selection

## 10. Notebook readiness

## 11. Atomic import and replay prevention

## 12. Release self-containment

## 13. Validation results

Give exact commands, exits, and test totals.

## 14. Remaining external blockers

## 15. Exact next sequence

The next step must be real Kaggle smoke, not another repair prompt.

## 16. Runtime estimates

## 17. CVPR readiness scores

Separate:

- scientific design;
- engineering;
- runtime;
- evidence;
- paper;
- release.

## 18. Files created or modified

## 19. Master continuation point

Point to:

```text
CERTVIC_CVPR_EXECUTION_MASTER_PLAN.md
reports/cvpr_run_readiness/CERTVIC_READY_TO_RUN_HANDOFF.md
```

---

# 8. Success standard

This task succeeds only when the next real action is:

1. attach wheelhouse bytes;
2. attach verified model snapshots;
3. run 00A;
4. run 00B;
5. run 00C2 for Qwen, InternVL, and LLaVA;
6. return smoke ZIPs;
7. authorize and run the confirmatory study.

There must be no remaining local implementation prompt after this pass.

Do not declare readiness from isolated tests.

**Close the final portability, authorization, smoke, detectability, and exact-selection gaps, prove every route synthetically, and leave CertVIC ready to run.**
