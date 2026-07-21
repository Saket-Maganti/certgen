# CERTGEN — FINAL RUN-READY CLOSURE, LIVE BUILDER REPAIR, FEATURE-PACKAGING FIX, AND CVPR VALUE UPGRADE

You are GPT‑5.6 Sol operating as:

- a senior computer-vision researcher;
- a generative-model evaluation researcher;
- a sequential-inference specialist;
- a research software architect;
- a Kaggle T4×2 execution engineer;
- a reproducibility and artifact-integrity auditor;
- a CVPR reviewer focused on scientific value, execution continuity, and evidence honesty.

You have full access to the live repository:

```text
/Users/saketmaganti/Projects/certGen
```

Your task is to perform the **final run-ready closure and CVPR-value upgrade pass** for CertGen.

This is not another broad architecture rewrite.

This is not a new V10/V11/V12 layer.

Do not create a parallel pipeline.

Work directly on the canonical CVPR pipeline and repair the remaining live defects that prevent a real execution from flowing continuously through:

```text
reference validation
→ reference materialization
→ selectable model/extractor preflight package
→ real Kaggle T4×2 model/extractor preflight
→ preflight import
→ generation package
→ real 1k generation
→ generation import
→ feature package containing resolvable images
→ feature extraction
→ feature import
→ feature merge into cache-v2
→ metric reproduction
→ sanity gates
→ frozen comparison family
→ certificate
→ certified partial ranking
→ cross-feature analysis
→ stop-and-interpret gate
```

The final repository must be honestly ready to begin the real CIFAR run.

Do not run real datasets, checkpoints, Kaggle jobs, generation, feature extraction, metric reproduction, certificates, or empirical paper analyses during this pass.

No fabricated evidence.

No `claim_allowed=true`.

---

# 1. Current verified state

The current project has:

- a defensible bounded RBF-MMD statistical core;
- union-Hoeffding time-uniform confidence sequences;
- Bonferroni family-wise control;
- cache-v2 contracts;
- secure importers;
- five canonical Kaggle notebooks;
- subprocess GPU workers;
- per-GPU scheduling infrastructure;
- real model/extractor preflight code;
- adapter capability registries;
- output schemas;
- feature merge logic;
- evidence gates;
- partial-ranking infrastructure;
- synthetic runtime tests;
- a clean reproducibility archive;
- paper and release firewalls.

The latest closure pass reportedly reached:

```text
CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT
```

A follow-up audit found that this is still too optimistic because the **live registry-to-builder-to-feature-package path remains discontinuous**.

The current honest state is:

```text
CVPR_CORE_AND_RUNTIME_CONTRACTS_VALID
REAL_RUN_HANDOFF_PARTIAL
BLOCKED_BY_REFERENCE_INPUT_AND_LIVE_BUILDER_DEFECTS
```

The expected final state, only if earned, is:

```text
CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT
```

---

# 2. Scientific boundary

The rigorous route remains:

- fixed prospective visual evaluation protocol;
- bounded RBF-MMD difference stream;
- direct pairwise comparison contributions;
- non-overlapping sample construction;
- conservative support bounds;
- union-Hoeffding time-uniform confidence sequence;
- first-crossing directional decisions;
- Bonferroni family-wise control;
- partial rankings rather than forced total rankings;
- FID/FD descriptive unless separately justified;
- polynomial KID not automatically certified;
- no metric-agnostic claims;
- no paper evidence before real execution.

Do not expand the claim surface.

Do not promote unsupported statistical routes.

---

# 3. Confirmed live defects that must be repaired

Treat these findings as confirmed unless the live repository proves they are already fixed.

## 3.1 Preflight builder cannot select a viable pilot subset

The live registry may contain:

- two usable or potentially usable DDPM candidates;
- one blocked CFM candidate;
- Inception and CLIP candidates;
- unresolved DINO planning rows.

The current preflight builder may treat every blocked registry row as a global failure.

This prevents a valid minimum pilot from being prepared.

### Required fix

Support explicit prospective selection:

```bash
python3 -m certgen prepare preflight \
  --models <comma-separated-model-ids> \
  --extractors <comma-separated-extractor-ids>
```

The builder must:

- include only explicitly selected rows;
- validate those rows fully;
- preserve excluded rows as registered-but-not-selected;
- refuse post hoc selection based on outcomes;
- write the selected pilot profile into the frozen config;
- block only when a selected row is invalid.

Create named profiles:

```text
cifar_integrity_minimal
cifar_integrity_modern
cifar_full_candidate
```

Example minimum profile:

```text
2 validated DDPM-family models
Inception
CLIP
1k generation
1k reference draw
claim_allowed=false
pilot_only
```

DINO and CFM may remain excluded until their own preflight succeeds.

---

## 3.2 Inception asset acquisition and local loading are incomplete

A generic Hugging Face asset path cannot be used for Torchvision Inception weights.

### Required fix

Implement a dedicated Inception asset adapter that:

- resolves the exact Torchvision weight enum;
- records the Torchvision package version;
- obtains or validates the exact weight file during online preflight;
- stores the file under a canonical asset root;
- records SHA-256;
- records expected feature dimension;
- records the exact preprocessing transform;
- supports offline local loading during feature extraction;
- never silently downloads during an offline extraction run.

The extractor worker must load the validated local weight file, not rely on an implicit Torchvision cache or network fallback.

---

## 3.3 CLIP extractor uses an ambiguous or incorrect model interface

The current generic `AutoModel` path may not clearly define the image feature being used.

### Required fix

Implement a dedicated CLIP image-feature adapter.

Freeze one explicit estimand:

```text
projected image embedding
```

or:

```text
vision pooler output
```

or:

```text
CLS hidden state
```

Choose exactly one primary CLIP representation for the pilot.

Record:

```text
model class
processor class
revision
feature definition
pre-normalization dimension
post-normalization dimension
projection applied
L2 normalization applied
expected output dimension
```

The same definition must be used in:

- preflight;
- feature extraction;
- cache-v2 sidecar;
- paper metric capability registry;
- family configuration.

Do not call the representation “CLIP features” without specifying which output.

---

## 3.4 DINO remains unresolved but may block the pilot

### Required fix

Keep DINO as an optional expansion lane.

Do not allow an unresolved DINO row to block:

```text
cifar_integrity_minimal
```

If DINO is selected, require:

- exact model identifier;
- exact revision;
- exact implementation package;
- exact feature definition;
- exact output dimension;
- exact preprocessing;
- successful real extractor preflight.

If not selected, leave it:

```text
REGISTERED_NOT_SELECTED
claim_allowed=false
```

---

## 3.5 Feature worker does not load the exact validated local snapshot

Preflight may validate a direct local snapshot, while the feature worker later calls the remote model ID with `cache_dir`.

### Required fix

The feature worker must consume the exact preflight-approved asset manifest and load:

```text
snapshot_path
```

directly.

The asset manifest must bind:

```text
extractor_id
source_repo
revision
snapshot_path
layout_type
loader_type
file_hashes
preflight_status
```

Reject extraction if the local snapshot differs from the preflight manifest.

---

## 3.6 Extractor batch calibration is not truthful

Testing a requested batch size of 64 with only eight fixture images is not a real calibration of 64.

### Required fix

For every candidate batch size:

- create or replicate exactly that many fixture images;
- run the full preprocessing and forward pass;
- verify output count equals requested count;
- measure peak VRAM;
- record elapsed time;
- fail or reduce on OOM;
- record the largest actually tested successful batch size.

The final report must distinguish:

```text
tested_batch_size
selected_batch_size
fallback_batch_size
```

Never report a safe batch size larger than the actual tested image count.

---

## 3.7 Generation image manifest and feature preparation use different field names

Generation may write:

```text
path
```

while feature preparation expects:

```text
image_path
```

Feature shards may use:

```text
source_path
```

while workers read:

```text
image_path
```

### Required fix

Create one shared image-manifest schema.

Use one canonical field:

```text
relative_image_path
```

Required fields:

```text
sample_id
role
model_id
relative_image_path
image_hash
seed
prompt_or_class_id
width
height
mode
source_run_id
source_manifest_hash
```

The same schema must drive:

- generation writer;
- generation importer;
- feature preparation;
- feature worker;
- feature merge;
- cache sidecar;
- tests.

No handwritten field-name translation in separate modules.

---

## 3.8 Feature package does not contain resolvable images

The feature package may contain manifests that point to local Mac paths.

Those paths do not exist on Kaggle.

### Required fix

Support two explicit feature-input modes:

```text
EMBED_IMAGES_IN_PACKAGE
MOUNT_EXTERNAL_IMAGE_DATASET
```

For the 1k CIFAR pilot, default to:

```text
EMBED_IMAGES_IN_PACKAGE
```

Package:

```text
images/reference/
images/<model_id>/
```

Rewrite all manifest paths to canonical relative paths inside the package.

For larger scales, support external mounted datasets with:

```text
mount_id
expected_mount_path
mount_manifest_hash
```

The notebook must validate every image path before GPU allocation.

---

## 3.9 Real builders are not exercised by the synthetic end-to-end test

The 21-stage synthetic test may construct objects directly instead of using:

```text
prepare preflight
prepare generation
prepare features
prepare family
```

### Required fix

Create a **builder-faithful synthetic closure test** that executes the actual canonical CLI or underlying builder functions using temporary fixture registries and fixture artifacts.

The test must prove:

```text
selected pilot profile
→ preflight input ZIP
→ fake preflight output ZIP
→ import
→ generation input ZIP
→ fake generation output ZIP
→ import
→ feature input ZIP with embedded images
→ fake feature output ZIP
→ import
→ merge
→ cache-v2
→ family freeze
→ certificate
→ partial ranking
```

Do not use a simplified side route.

---

# 4. Additional defects to re-check

Re-verify that earlier repaired defects remain closed:

- one active worker per GPU;
- unsupported CFM remains blocked;
- model-family-specific adapters apply frozen generation config;
- local snapshot loading is used;
- dependency and model-asset network policies are separate;
- notebook ZIP schema matches importer;
- feature merge writes cache-v2;
- `prepare family` uses real registry fields;
- resume markers validate hashes;
- final ZIP reuse/rebuild is idempotent;
- portable archive passes without `.git`;
- all current docs point to the canonical execution handbook.

If any regressed, repair them.

---

# 5. Non-negotiable restrictions

Do not:

- download CIFAR;
- download real model checkpoints during local tests;
- run Kaggle;
- run Colab;
- run CUDA-dependent tests;
- run real model generation;
- run real feature extraction;
- create empirical metric values;
- run claim-bearing certificates;
- populate paper result tables;
- set `claim_allowed=true`;
- fabricate licenses;
- fabricate model support;
- fabricate runtime measurements.

Allowed:

- fake model adapters;
- tiny synthetic images;
- fixture checkpoints;
- fixture extractor snapshots;
- local CPU tests;
- deterministic package creation;
- secure importer tests;
- synthetic end-to-end runtime;
- notebook static analysis;
- paper compilation;
- archive verification.

All fixture outputs must remain:

```text
synthetic_validation_only
not_model_evidence
claim_allowed=false
```

---

# 6. Phase A — Reproduce baseline

Run all local-safe checks before editing.

Record:

```text
command
working_directory
start_time
end_time
duration
exit_code
passed
failed
skipped
warnings
```

Create or update:

```text
reports/CERTGEN_FINAL_RUN_READY_BASELINE.md
reports/CERTGEN_FINAL_RUN_READY_COMMAND_LEDGER.csv
reports/CERTGEN_FINAL_RUN_READY_CURRENT_STATE.json
```

Baseline checks:

- compileall;
- imports;
- default non-recursive pytest;
- integration audits;
- statistical lane;
- artifact-contract lane;
- runtime-hardening lane;
- real-execution-closure lane;
- notebook static analyzer;
- deterministic notebook regeneration;
- CVPR audit;
- forensic audit;
- V9 compatibility;
- paper firewall;
- privacy scan;
- release scan;
- Ruff;
- critical mypy;
- full mypy debt comparison;
- paper build;
- `git diff --check`.

---

# 7. Phase B — Pilot profile and selection system

Implement:

```bash
python3 -m certgen profiles list
python3 -m certgen profiles show <profile>
python3 -m certgen prepare preflight --profile <profile>
```

Each profile must freeze:

```text
benchmark
models
extractors
sample scale
reference count
generation count
feature spaces
metrics
comparison family
evidence class
claim permission
```

Profiles:

## 7.1 `cifar_integrity_minimal`

Purpose:

- prove end-to-end lineage and runtime;
- no paper claim.

Suggested structure:

```text
2 validated DDPM-family models
Inception
CLIP
1k samples/model
1k reference draw
null control
obvious-gap control
contestable model pair
pilot_only
claim_allowed=false
```

## 7.2 `cifar_integrity_modern`

Adds:

- DINO only if validated;
- additional comparison/sensitivity lanes.

## 7.3 `cifar_full_candidate`

May include:

- CFM only after adapter preflight;
- more feature spaces;
- larger sample budget.

The profile builder must not silently change membership after results are observed.

---

# 8. Phase C — Dedicated extractor adapters

Implement dedicated adapters for:

```text
Inception
CLIP
DINO optional
```

Each adapter must expose:

```text
resolve_asset()
load()
observed_preprocessing()
extract_batch()
output_definition()
output_dimension()
normalize()
unload()
```

Each adapter must produce:

```text
requested_contract
observed_contract
difference_report
preflight_status
```

Fail before extraction on any claim-relevant mismatch.

---

# 9. Phase D — Unified image manifest

Create:

```text
schemas/cvpr/image_manifest.schema.json
```

or one canonical typed Python schema.

Use it everywhere.

Required validation:

- unique sample IDs;
- valid relative paths;
- no absolute paths;
- no traversal;
- file exists;
- image hash matches;
- role valid;
- model ID valid;
- dimensions valid;
- mode valid;
- source lineage present.

Add migration helpers only for historical manifests.

Do not allow new code to emit legacy fields.

---

# 10. Phase E — Feature package builder

Complete:

```bash
python3 -m certgen prepare features
```

Inputs:

- materialized reference;
- imported generation artifacts;
- selected pilot profile;
- successful extractor preflight;
- extractor asset manifests;
- preprocessing contracts.

Outputs:

```text
feature_config.yaml
profile_snapshot.yaml
role_manifest.csv
image_manifest.jsonl
reference_draw_plan.json
extractor_configs/
asset_manifests/
preprocessing_contracts/
image_shards/
images/ or mount_manifest.json
expected_output_schema.json
run_identity.json
KAGGLE_INSTRUCTIONS.md
certgen_cvpr_feature_input_<run_id>.zip
```

For the 1k pilot, embed images.

The local pre-upload validator must open and decode every image.

---

# 11. Phase F — Real package continuity test

Create tests that use the exact package and import contracts.

Required cases:

- minimum profile succeeds;
- blocked CFM excluded;
- unresolved DINO excluded;
- selected blocked model fails;
- selected blocked extractor fails;
- generation manifest feeds feature builder;
- image paths resolve after ZIP extraction;
- feature worker reads every image;
- output ZIP imports;
- feature merge succeeds;
- cache-v2 validates;
- family freezes.

---

# 12. Phase G — CVPR-value upgrades

Implement only additions that materially improve the future paper and can be prepared before real results.

## 12.1 Cross-feature agreement/disagreement analysis

Build an analysis module that consumes completed certificates across:

- Inception;
- CLIP;
- DINO when available.

Outputs:

```text
agreement_matrix.csv
direction_disagreements.csv
decided_in_one_unresolved_in_another.csv
consensus_edges.json
feature_specific_edges.json
```

Rules must be prospectively defined.

Do not call disagreements errors.

## 12.2 Ranking stability across sample budgets

Build analysis for:

```text
1k
10k
50k
```

Outputs:

- edge appearance budget;
- edge disappearance if protocol differs;
- unresolved-at-budget status;
- partial-order stability;
- first-decision sample count.

Do not fabricate values.

## 12.3 Point leaderboard versus certified partial ranking

Prepare one canonical comparison artifact:

```text
point_estimate_total_order
certified_direct_edges
transitive_implications
unresolved_pairs
invalid_pairs
```

This is a central CVPR-value figure contract.

## 12.4 Real compute-accounting contract

Prepare fields for:

```text
images generated
images feature-extracted
GPU seconds
CPU seconds
samples at first decision
fixed-budget samples
retrospective savings
online realized savings
```

Keep retrospective and realized savings separate.

## 12.5 Qualitative model-pair gallery contract

Prepare a gallery generator that can later show:

- representative images;
- model IDs;
- feature-space decisions;
- point-estimate direction;
- certificate status;
- first-decision sample count;
- limitations.

Images must never be presented as proof of distribution-level superiority.

## 12.6 Preregistration freeze command

Add:

```bash
python3 -m certgen freeze study --profile <profile>
```

It must freeze:

- models;
- extractors;
- benchmark;
- reference draw;
- feature definitions;
- preprocessing;
- metrics;
- bandwidth;
- alpha;
- comparison family;
- budgets;
- scale-up rules;
- exclusion rules.

No result-bearing stage may proceed without a frozen study hash.

## 12.7 Adapter conformance matrix

Generate:

```text
reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv
```

Fields:

```text
adapter
model_or_extractor
asset_resolution
load
smoke
batching
seed_mapping
preprocessing
output_dimension
resume
offline_loading
status
blocker
```

This increases reviewer confidence and reduces execution risk.

---

# 13. Phase H — Runtime calibration upgrade

After real preflight, support ingestion of measured:

```text
download time
model load time
smoke generation time
images per second
peak VRAM
safe batch size
extractor images per second
```

Add:

```bash
python3 -m certgen runtime-plan ingest-preflight <report>
```

The planner must distinguish:

```text
PLANNING_ESTIMATE
MEASURED_PREFLIGHT
DERIVED_FROM_MEASURED_PREFLIGHT
```

This is execution metadata, not scientific evidence.

---

# 14. Phase I — Readiness command

Strengthen:

```bash
python3 -m certgen readiness
```

It must report separately:

```text
reference
selected profile
study freeze
model preflight package
extractor preflight package
model adapter readiness
extractor adapter readiness
generation package
feature package
image-path resolvability
output schema compatibility
feature merge
cache-v2
family freeze
exact next action
```

Possible final local state:

```text
RUN_READY_WAITING_FOR_REFERENCE
```

After reference materialization:

```text
READY_TO_PREPARE_PREFLIGHT
```

---

# 15. Phase J — Canonical notebooks

Regenerate all five notebooks.

Ensure:

## Preflight notebook

- supports profile selection;
- preflights only selected models/extractors;
- handles Inception through its dedicated asset adapter;
- handles CLIP through its dedicated image adapter;
- excludes unresolved DINO/CFM unless selected and valid;
- one worker per GPU;
- real smoke generation/features;
- truthful batch calibration;
- deterministic output ZIP.

## Generation notebook

- consumes the exact selected profile;
- loads validated local snapshots;
- uses adapter-specific config;
- writes the unified image manifest;
- records applied config;
- preserves seed mapping;
- supports resume and ZIP recovery.

## Feature notebook

- consumes embedded images or validated mount manifest;
- resolves only relative package paths;
- loads validated local extractor snapshots;
- uses dedicated adapters;
- writes shard outputs compatible with merge;
- preserves unified sample IDs and role metadata.

---

# 16. Phase K — Portable archive

The final archive must include:

- root README;
- LICENSE;
- CITATION.cff;
- pyproject.toml;
- `.gitignore`;
- canonical notebooks;
- schemas;
- builders;
- importers;
- tests;
- final report;
- final handbook;
- required audit reports.

Exclude:

- `.git`;
- ADE20K;
- raw datasets;
- model caches;
- Mac metadata;
- Python caches;
- quarantine;
- local user paths.

Portable tests must not require `.git`.

---

# 17. Phase L — Full verification

Run:

```text
compileall
imports
default tests
integration audits
statistical lane
artifact-contract lane
runtime-hardening lane
real-execution-closure lane
new pilot-profile tests
new extractor-adapter tests
new image-manifest tests
new feature-package tests
builder-faithful synthetic closure
cross-feature analysis fixture tests
ranking-stability fixture tests
preregistration freeze tests
adapter conformance tests
notebook static analyzer
deterministic notebook regeneration
portable archive tests
CLI readiness tests
paper firewall
privacy scan
release scan
Ruff
critical mypy
full mypy debt comparison
paper compilation
git diff --check
CVPR audit
forensic audit
V9 compatibility audit
```

No test may use:

- internet;
- real CIFAR;
- real checkpoints;
- CUDA;
- real paper evidence.

---

# 18. Final status taxonomy

Choose exactly one:

```text
FINAL_RUN_READY_CLOSURE_FAILED
FINAL_RUN_READY_CLOSURE_PARTIAL
FINAL_RUN_READY_BLOCKED_BY_LOCAL_DEFECT
CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT
CVPR_REFERENCE_READY_PREFLIGHT_PACKAGE_REQUIRED
CVPR_REAL_PREFLIGHT_READY
```

Expected, only if earned:

```text
CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT
```

---

# 19. Required final artifacts

Create:

```text
CERTGEN_CVPR_FINAL_RUN_READY_CLOSURE_REPORT.md
CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md

reports/CERTGEN_FINAL_RUN_READY_BASELINE.md
reports/CERTGEN_FINAL_RUN_READY_COMMAND_LEDGER.csv
reports/CERTGEN_FINAL_RUN_READY_CURRENT_STATE.json
reports/CERTGEN_FINAL_RUN_READY_REPAIR_CHANGELOG.md
reports/CERTGEN_FINAL_RUN_READY_TEST_MATRIX.md
reports/CERTGEN_FINAL_RUN_READY_NOTEBOOK_READINESS.md
reports/CERTGEN_FINAL_RUN_READY_HANDOFF_AUDIT.md
reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv

docs/execution/CERTGEN_PILOT_PROFILE_PROTOCOL.md
docs/execution/CERTGEN_INCEPTION_ASSET_ADAPTER.md
docs/execution/CERTGEN_CLIP_FEATURE_DEFINITION.md
docs/execution/CERTGEN_IMAGE_MANIFEST_CONTRACT.md
docs/execution/CERTGEN_FEATURE_IMAGE_PACKAGING_PROTOCOL.md
docs/execution/CERTGEN_BUILDER_FAITHFUL_SYNTHETIC_TEST.md
docs/analysis/CERTGEN_CROSS_FEATURE_AGREEMENT_PROTOCOL.md
docs/analysis/CERTGEN_RANKING_STABILITY_PROTOCOL.md
docs/analysis/CERTGEN_POINT_VS_CERTIFIED_RANKING_CONTRACT.md
docs/analysis/CERTGEN_COMPUTE_ACCOUNTING_CONTRACT.md
docs/analysis/CERTGEN_QUALITATIVE_GALLERY_CONTRACT.md
```

Mark older handbooks as superseded.

---

# 20. Final report requirements

The final report must state:

1. whether the minimum pilot can be prepared from the current registries;
2. which models are selected;
3. which extractors are selected;
4. which rows remain registered but excluded;
5. whether Inception offline loading is verified by fixtures;
6. whether the CLIP feature definition is explicit;
7. whether generation and feature manifests share one schema;
8. whether feature images are resolvable on Kaggle;
9. whether the real builders pass end-to-end synthetic execution;
10. whether cross-feature analysis contracts exist;
11. whether preregistration freezing works;
12. whether any known local defect remains;
13. the exact blocker;
14. the exact next command;
15. whether any further pre-run patch is justified.

The desired stop-building conclusion, only if earned:

> No further broad or targeted pre-run infrastructure development is justified. The repository is ready for official CIFAR reference validation, materialization, study freeze, and the first real Kaggle preflight.

---

# 21. Exact execution handbook path

The final handbook must describe:

1. place CIFAR archive;
2. validate reference;
3. materialize reference;
4. select pilot profile;
5. freeze study;
6. prepare preflight package;
7. validate preflight input;
8. run Kaggle preflight;
9. validate output;
10. import preflight;
11. ingest runtime calibration;
12. prepare generation package;
13. validate input;
14. run 1k generation;
15. validate and import output;
16. prepare feature package with embedded images;
17. validate feature input;
18. run feature extraction;
19. validate and import output;
20. merge features;
21. validate cache-v2;
22. metric reproduction;
23. sanity gates;
24. family freeze;
25. certificate;
26. partial ranking;
27. cross-feature analysis;
28. stop and interpret.

For every step include:

```text
command
location
CPU_or_GPU
network policy
input
output
runtime class
resume
failure recovery
evidence class
claim permission
completion test
```

---

# 22. Stop-building rule

After this pass, stop building.

Only patch further if real execution reveals:

- real model-load failure;
- real extractor-load failure;
- Kaggle dependency failure;
- unexpected OOM;
- local snapshot incompatibility;
- output import failure;
- feature path failure;
- cache-v2 failure;
- metric reproduction failure;
- evidence gate defect.

Do not build:

- new theory;
- e-BH;
- FID certification;
- video;
- dashboards;
- cloud orchestration;
- plugin marketplaces;
- manuscript automation;
- another broad prompt.

---

# 23. Completion condition

This task is complete only when:

1. baseline is reproduced;
2. a viable minimum pilot profile can be prepared;
3. blocked CFM does not block the pilot;
4. unresolved DINO does not block the pilot;
5. Inception has a dedicated offline asset adapter;
6. CLIP has a dedicated explicit image-feature adapter;
7. extractor calibration is truthful;
8. one image-manifest schema is used everywhere;
9. feature packages contain resolvable images;
10. the actual builders pass end-to-end synthetic execution;
11. feature merge produces valid cache-v2;
12. family freeze succeeds;
13. preregistration freeze succeeds;
14. cross-feature and ranking-stability analysis contracts exist;
15. all local-safe tests and audits pass;
16. the portable archive passes;
17. the final status is reported;
18. one exact next command is reported;
19. the report states whether any further pre-run patch is justified.

Begin now by inspecting the live repository and reproducing the baseline. Do not write the final verdict before verifying the implementation.
