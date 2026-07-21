# CERTGEN — PHASE 2: RESUME AFTER EACH KAGGLE OUTPUT, COMPLETE EVERY CPU BRIDGE, BUILD THE NEXT GPU BUNDLE, AND FINISH THE 1K PIPELINE

You are GPT‑5.6 Codex operating as a secure artifact importer, CPU pipeline orchestrator, scientific-computing execution engineer, sequential-inference auditor, and CVPR evidence-integrity reviewer.

Repository:

```text
/Users/saketmaganti/Projects/certGen
```

This is a **reusable resume prompt**.

Run this same prompt after any real Kaggle output ZIP has been downloaded and placed into the canonical incoming location.

Supported returned stages:

```text
environment diagnostic
model/extractor preflight
image generation
feature extraction
```

Your job is to:

1. discover the new returned artifact;
2. validate it securely;
3. import it;
4. run every available CPU stage;
5. build the next real Kaggle upload ZIP;
6. stop at the next GPU boundary;
7. after feature output, continue automatically through all remaining CPU analysis and finish the 1k pilot.

Do not ask which stage was returned when repository state and package metadata identify it unambiguously.

The prompt must be safe to run repeatedly.

Choose exactly one final status:

```text
WAITING_FOR_KAGGLE_DIAGNOSTIC
WAITING_FOR_KAGGLE_PREFLIGHT
WAITING_FOR_KAGGLE_GENERATION
WAITING_FOR_KAGGLE_FEATURES
SCIENTIFIC_GATE_FAILED
FULL_1K_CPU_ANALYSIS_COMPLETE
LOCAL_DEFECT_REMAINS
INVALID_RETURNED_KAGGLE_ARTIFACT
```

Desired result after feature output:

```text
FULL_1K_CPU_ANALYSIS_COMPLETE
```

---

# 1. Truthfulness boundary

Do not:

- run Kaggle or Colab;
- initialize CUDA locally;
- download reference data or checkpoints;
- fabricate missing outputs;
- treat fixture outputs as real;
- weaken validators;
- bypass metric or sanity gates;
- change seeds, models, features, budgets, or family membership to force a pass;
- set `claim_allowed=true` without the repository’s real-evidence rules permitting it;
- populate paper claims beyond validated evidence.

Allowed:

- local CPU validation/import;
- safe archive extraction;
- hashing;
- runtime-calibration ingestion;
- control construction;
- next-stage upload-ZIP creation;
- cache merging;
- metric and sanity gates;
- CPU certificate execution;
- ranking;
- cross-feature analysis;
- provenance, replay, accounting, claims, and reports.

Use a CPU-only environment where compatible:

```text
CUDA_VISIBLE_DEVICES=""
CERTGEN_CPU_ONLY=1
```

---

# 2. Preserve live state

Before execution:

- record Git branch and HEAD;
- record `git status --short`;
- preserve user changes;
- do not reset or clean;
- do not delete returned ZIPs;
- do not overwrite valid immutable artifacts;
- do not remove the official CIFAR archive.

Create or append to:

```text
reports/CERTGEN_CPU_EXECUTION_COMMAND_LEDGER.csv
reports/CERTGEN_CPU_EXECUTION_COMMAND_LEDGER.jsonl
```

Record:

```text
sequence
stage
command
cwd
start_utc
end_utc
duration_seconds
exit_code
stdout_log
stderr_log
status
artifacts_created
artifacts_reused
blocker
```

---

# 3. Discover current state

Run:

```bash
python3 -m certgen readiness --explain --json
python3 -m certgen next-action --explain
python3 -m certgen doctor --json
python3 -m certgen kaggle next --explain
```

Require these views to agree.

Inspect canonical incoming/output paths and the artifact registry.

Classify the newest returned package as:

```text
DIAGNOSTIC_OUTPUT
PREFLIGHT_OUTPUT
GENERATION_OUTPUT
FEATURE_OUTPUT
NONE
AMBIGUOUS
INVALID
```

Use package metadata, not filename guessing.

---

# 4. Secure ZIP validation

For each candidate:

1. inspect without extraction;
2. reject traversal;
3. reject absolute paths;
4. reject symlinks;
5. validate package type;
6. validate run identity;
7. validate study/profile/configuration hashes;
8. validate worker contract;
9. validate dependency report;
10. validate asset report;
11. validate completion markers;
12. validate member hashes;
13. validate expected row or seed coverage;
14. reject stale, duplicate, partial, or ambiguous outputs;
15. import only after all checks pass.

Do not import fixture packages as real.

Quarantine invalid ZIPs and report the exact reason.

---

# 5. Diagnostic return

If a valid diagnostic output exists:

- import it;
- register the Kaggle environment record;
- verify two T4 GPUs;
- verify dependency mode;
- verify disk/write/multiprocessing checks;
- update dependency compatibility observations;
- update runtime assumptions using measured values;
- rebuild and validate the preflight input ZIP if operational settings changed;
- update the launchboard.

Stop with:

```text
WAITING_FOR_KAGGLE_PREFLIGHT
```

Report:

```text
preflight input ZIP
ZIP hash
preflight notebook
accelerator GPU T4 ×2
internet mode
private assets
estimated runtime
expected output ZIP
local copy-back path
exact resume command
```

If diagnostic is optional or already satisfied, continue according to canonical state.

---

# 6. Preflight return

If a valid model/extractor preflight output exists:

- import it;
- register model and extractor readiness;
- ingest measured model load times;
- ingest warmup and throughput;
- ingest safe batch sizes;
- ingest peak VRAM;
- append measured calibration records;
- preserve historical planning estimates;
- verify selected models and extractors passed;
- verify asset hashes and revisions;
- fail closed on required model/extractor failure;
- build the real 1k generation input ZIP;
- validate the ZIP;
- create/verify its run capsule;
- create/verify its sidecar;
- update the launchboard;
- verify provenance;
- verify replay.

Expected ZIP:

```text
artifacts/cvpr/kaggle_inputs/generation/certgen_cvpr_generation_1k_input.zip
```

Stop with:

```text
WAITING_FOR_KAGGLE_GENERATION
```

Report:

```text
generation input ZIP
ZIP hash
generation notebook
accelerator GPU T4 ×2
internet mode
measured runtime estimate
expected output ZIP
local copy-back path
exact resume command
```

---

# 7. Generation return

If a valid generation output exists:

- import it;
- validate exact model coverage;
- validate exact seed coverage;
- reject duplicates and omissions;
- validate image decoding;
- validate dimensions and color mode;
- validate hashes;
- validate checkpoint/model identity;
- validate manifests;
- register generated-image artifacts;
- build the deterministic null control;
- build the deterministic obvious-gap control;
- validate control manifests;
- build the real feature input ZIP;
- validate the ZIP;
- create/verify its run capsule;
- create/verify its sidecar;
- update the launchboard;
- verify provenance;
- verify replay.

Expected ZIP:

```text
artifacts/cvpr/kaggle_inputs/features/certgen_cvpr_features_input.zip
```

Stop with:

```text
WAITING_FOR_KAGGLE_FEATURES
```

Report:

```text
feature input ZIP
ZIP hash
feature notebook
accelerator GPU T4 ×2
internet mode
private extractor assets
estimated runtime
expected output ZIP
local copy-back path
exact resume command
```

---

# 8. Feature return

If a valid feature output exists:

- import it;
- validate Inception outputs;
- validate CLIP outputs;
- validate reference, generated, null-control, and obvious-gap roles;
- validate exact row coverage;
- reject duplicate and missing rows;
- validate preprocessing hashes;
- validate extractor revisions;
- validate dimensions and dtypes;
- validate shard manifests;
- register feature artifacts;
- merge shards into cache-v2;
- validate all caches;
- register merged caches.

Do not stop after feature import.

Continue automatically through every remaining CPU stage.

---

# 9. Metric and sanity gates

After valid caches exist:

- freeze metric-reproduction configuration;
- freeze sanity-gate configuration;
- run metric reproduction;
- run null-control checks;
- run obvious-gap checks;
- verify direction and preprocessing status;
- require prospectively defined pass criteria.

If a required gate fails:

```text
SCIENTIFIC_GATE_FAILED
```

Preserve diagnostics and stop.

Do not weaken thresholds.

---

# 10. Family and certificate inputs

After gates pass:

- freeze the confirmatory family;
- verify multiplicity allocation;
- build every certificate-input bundle;
- validate all bundles;
- validate operational family completeness;
- reject missing or extra bundles.

Require the complete registered minimum-pilot family.

---

# 11. Execute all CPU certificates

- execute every missing certificate;
- reuse only hash-valid completed certificates;
- verify family coverage;
- create lineage cards;
- verify alpha allocation;
- verify sample budgets;
- verify first-crossing and censoring fields;
- reject duplicate or unregistered results.

Do not stop after the first certificate.

---

# 12. Build the partial ranking

- require complete certificate coverage or frozen exclusions;
- build a certified partial ranking;
- reject forced total ordering;
- produce:

```text
ranking_graph.json
ranking_edges.csv
ranking_unresolved.csv
ranking_invalid.csv
ranking_provenance.json
```

Every edge must link to supporting certificate IDs.

---

# 13. Cross-feature analysis

Produce:

```text
agreement_matrix.csv
direction_disagreements.csv
decided_vs_unresolved.csv
invalid_feature_lanes.csv
consensus_edges.json
representation_specific_edges.json
```

Apply the prospectively frozen policy.

Do not label representation disagreement as implementation failure unless contracts differ.

---

# 14. Final CPU products

Complete:

- accounting summary;
- provenance graph and verification;
- deterministic replay plan;
- prospective sensitivity outputs;
- claim-evidence validation;
- paper firewall;
- figure/table data-contract validation;
- pilot stop/go report;
- final readiness report;
- final artifact inventory.

Do not promote to 10k, 50k, DINO, CFM, or a second benchmark unless the frozen stop/go decision permits it.

---

# 15. Reusable autorun

Prefer:

```bash
cd /Users/saketmaganti/Projects/certGen

python3 scripts/run_all_available_cpu_stages.py \
  --resume \
  --explain
```

If incomplete, repair it narrowly.

It must:

- discover returned ZIPs;
- validate/import them;
- complete all available CPU work;
- build the next GPU ZIP;
- stop at the correct boundary;
- complete final analysis after features;
- be idempotent;
- be resumable;
- never use GPU;
- never promote fixtures.

Exit codes:

```text
0  CPU_AVAILABLE_STAGES_COMPLETE
11 WAITING_FOR_KAGGLE_DIAGNOSTIC
12 WAITING_FOR_KAGGLE_PREFLIGHT
13 WAITING_FOR_KAGGLE_GENERATION
14 WAITING_FOR_KAGGLE_FEATURES
20 SCIENTIFIC_GATE_FAILED
30 LOCAL_DEFECT
40 INVALID_RETURNED_KAGGLE_ARTIFACT
```

---

# 16. Runtime recording

Append real CPU durations.

Maintain labels:

```text
PLANNING_ESTIMATE_NOT_MEASURED
MEASURED_KAGGLE_PREFLIGHT
MEASURED_REAL_RUN
DERIVED_FROM_MEASURED_RUN
```

Do not present planning estimates as measured.

Update the launchboard after every stage.

---

# 17. Verification after each resume

Run focused checks for the affected stage, then:

- compileall;
- imports;
- relevant tests;
- provenance verify;
- replay verify;
- readiness;
- next-action;
- doctor;
- Kaggle-next;
- `git diff --check`.

After final completion also run:

- full unique local test suite;
- explicit integration audit;
- Ruff;
- critical mypy;
- full mypy debt comparison;
- notebook deterministic check;
- privacy scan;
- release scan;
- paper firewall;
- final pre-run audit;
- maximum-ceiling audit;
- CPU-execution audit;
- Kaggle-launch audit.

Do not recursively run the same full suite repeatedly.

---

# 18. Required reports

Create or update:

```text
CERTGEN_CPU_EXECUTION_AND_HANDOFF_REPORT.md
CERTGEN_CPU_NEXT_GPU_HANDOFF.md
CERTGEN_1K_PILOT_FINAL_EXECUTION_REPORT.md

reports/CERTGEN_CPU_EXECUTION_COMMAND_LEDGER.csv
reports/CERTGEN_CPU_EXECUTION_COMMAND_LEDGER.jsonl
reports/CERTGEN_CPU_EXECUTION_CURRENT_STATE.json
reports/CERTGEN_CPU_ARTIFACT_INVENTORY.csv
reports/CERTGEN_CPU_FINAL_AUDIT.md
reports/CERTGEN_KAGGLE_RUNTIME_ESTIMATES.csv
reports/CERTGEN_KAGGLE_FINAL_LAUNCH_AUDIT.md
```

At each GPU boundary, `CERTGEN_CPU_NEXT_GPU_HANDOFF.md` must contain:

```text
completed stage
next notebook
input ZIP
input ZIP hash
accelerator
internet mode
private assets
estimated runtime
expected output ZIP
local copy-back path
exact resume command
```

---

# 19. Final report

Answer:

1. Which returned ZIP was found?
2. Was it valid?
3. Was it imported?
4. Which CPU stages ran?
5. Which artifacts were created?
6. Which next upload ZIP was built?
7. Which notebook is next?
8. What is the estimated runtime?
9. Where should the next output ZIP be placed?
10. What exact resume command should be run?
11. If features were imported, did gates pass?
12. Were all certificates completed?
13. Was the partial ranking built?
14. Was cross-feature analysis completed?
15. Were claims unlocked or still blocked?
16. Does any local defect remain?
17. What is the final status?

Choose exactly one:

```text
WAITING_FOR_KAGGLE_DIAGNOSTIC
WAITING_FOR_KAGGLE_PREFLIGHT
WAITING_FOR_KAGGLE_GENERATION
WAITING_FOR_KAGGLE_FEATURES
SCIENTIFIC_GATE_FAILED
FULL_1K_CPU_ANALYSIS_COMPLETE
LOCAL_DEFECT_REMAINS
INVALID_RETURNED_KAGGLE_ARTIFACT
```

At a GPU boundary, do not recommend another build prompt. Print the exact next Kaggle action.

After final completion, do not expand the study unless the frozen stop/go decision permits it.

Begin now by recording repository state, querying readiness/next-action/doctor/kaggle-next, and securely discovering returned Kaggle output.
