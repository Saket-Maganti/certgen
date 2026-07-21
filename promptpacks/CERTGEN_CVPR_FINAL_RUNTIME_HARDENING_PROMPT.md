# CERTGEN — FINAL CVPR EXECUTION-HARDENING, KAGGLE T4×2 RUNTIME REPAIR, CANONICAL PIPELINE CONSOLIDATION, AND PRE-RUN SEAL

You are GPT‑5.6 Sol operating as:

- a senior computer-vision researcher;
- a generative-model evaluation researcher;
- a sequential-inference specialist;
- a research software architect;
- a Kaggle GPU workflow engineer;
- a reproducibility and artifact-integrity auditor;
- a CVPR reviewer focused on practical execution credibility.

You have full access to the local repository:

```text
/Users/saketmaganti/Projects/certGen
```

The repository has already undergone a broad CVPR-first pre-execution build and currently reports a strong local architecture, but a follow-up audit found several concrete runtime and integration gaps that could break the first real Kaggle execution.

Your task is to perform **one final surgical hardening pass** that repairs those gaps, strengthens the execution path, and brings the project as close as responsibly possible to a credible CVPR-ready pre-run state.

This is **not** another broad prompt-pack or generic architecture expansion.

Do not create V10/V11/V12 layers.

Work directly on the live repository.

Inspect, reproduce, repair, consolidate, test, and finish the existing canonical CVPR pipeline.

The goal is:

> After this pass, the only legitimate blockers should be real user-provided data, real checkpoint access, real Kaggle execution, real feature extraction, real statistical results, and real paper evidence.

No discoverable local/runtime-contract defect should remain unaddressed.

---

# 1. Current project state

The project currently reports:

```text
CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT
```

The follow-up audit refined the honest state to:

```text
CVPR_PREEXECUTION_ARCHITECTURE_COMPLETE
TARGETED_KAGGLE_RUNTIME_HARDENING_REQUIRED
BLOCKED_BY_REFERENCE_INPUT
```

Reported verification from the previous build includes:

```text
234 tests passed
31 statistical tests passed
25 artifact-contract tests passed
11 extended CVPR synthetic/gate tests passed
5 canonical notebooks passed static analysis
CVPR audit passed 8/8
Forensic audit passed 8/8
V9 compatibility audit passed 22/22
Paper compiled to 5 pages
Critical mypy lane passed
Historical mypy debt remained unchanged
No real experiments
No claim_allowed=true
```

The live repository is the source of truth. Reproduce or correct these facts.

The current rigorous scientific route remains:

- bounded RBF-MMD difference stream;
- direct per-step comparison contributions;
- support bounded conservatively;
- non-overlapping sample construction;
- union-Hoeffding time-uniform confidence sequence;
- first-boundary-crossing decision;
- Bonferroni family-wise control;
- FID/FD descriptive unless separately justified;
- polynomial KID not automatically certified;
- claim-safe evidence firewall;
- no empirical evidence yet.

Do not broaden statistical claims during this pass.

---

# 2. Known concrete defects that must be repaired

Treat the following as confirmed high-priority findings unless the live repository proves they have already been fixed.

## 2.1 Missing Kaggle environment bootstrap

The notebooks check pinned dependencies but do not contain a complete, idempotent setup/bootstrap flow.

Potentially affected packages include:

```text
torch
torchvision
diffusers
transformers
accelerate
safetensors
Pillow
numpy
scipy
scikit-learn
huggingface_hub
timm
open_clip_torch
```

The final notebooks must not merely fail with:

```text
pinned dependency mismatch
```

They must provide a real, explicit, reproducible environment bootstrap.

## 2.2 Inconsistent network/checkpoint policy

Current configs may declare:

```text
network_allowed: false
```

while the input packages do not actually contain all required:

- diffusion checkpoint caches;
- CLIP weights;
- DINO weights;
- Inception weights;
- tokenizer/config files;
- scheduler configs.

The project must choose and enforce one explicit policy per run:

```text
ONLINE_PREFLIGHT_DOWNLOAD
OFFLINE_PACKAGED_CACHE
```

Do not leave the notebooks in an ambiguous middle state.

## 2.3 Unsafe CUDA multiprocessing

The notebooks may import PyTorch or inspect CUDA in the parent notebook process and then use `fork`-based multiprocessing.

This can trigger CUDA reinitialization failures or incorrect GPU assignment.

Replace the CUDA runtime model with isolated worker subprocesses that set GPU visibility before importing PyTorch.

## 2.4 Generation not truly batched

The notebook/config may expose a batch size but generate one image at a time.

Implement real batched generation where the model API supports it.

Provide safe fallback for models that do not support deterministic per-image generators in a batch.

## 2.5 Declared preprocessing not proven at runtime

Feature configs may declare preprocessing rules without verifying that the actual processor/model pipeline applies exactly those rules.

Implement observed-preprocessing capture and equality checks.

## 2.6 Incomplete rerun/idempotence behavior

Notebooks may refuse to run if prior extracted inputs, output directories, or ZIPs exist, even when they belong to the same valid configuration.

Implement explicit:

```text
resume
restart
force-new-run
```

semantics.

## 2.7 Legacy dispatcher still points to old V6/V9 paths

The canonical CVPR stage machine and notebooks exist, but the next-action engine may still route later stages through older V6/V9 scripts and notebook names.

Unify execution guidance under the canonical CVPR CLI and notebook set.

## 2.8 Real-run configuration creation remains manual

Add canonical preparation commands that derive frozen runtime configs from validated registries and prior artifacts.

## 2.9 Recursive pytest architecture

Some audit tests launch full pytest inside pytest.

Remove recursive suite execution from the normal unit-test path.

## 2.10 Stale and contradictory documentation

Repair current guidance and mark historical reports as superseded where appropriate.

Examples include:

- stale ADE20K preservation claim;
- old V6 materialization commands;
- old notebook names;
- old benchmark choices;
- private absolute paths;
- old top-level status labels.

## 2.11 Archive/release cleanliness

The supplied archive contained or risked including:

```text
__MACOSX
.DS_Store
__pycache__
.pytest_cache
.ruff_cache
.mypy_cache
```

and may omit critical root files.

Build a canonical clean archive/export path.

---

# 3. Non-negotiable restrictions

## 3.1 No real scientific runs

Do not:

- download real datasets automatically;
- run CIFAR materialization on unavailable real input;
- download large checkpoints automatically during local validation;
- run Kaggle or Colab;
- run real GPU generation;
- run real feature extraction;
- import fabricated Kaggle outputs;
- run real model comparisons;
- run real certificates;
- generate empirical figures;
- produce paper result values;
- set `claim_allowed=true`.

## 3.2 Allowed local work

You may:

- run local CPU tests;
- run compilation;
- run static notebook analysis;
- execute fixture and synthetic tests;
- execute tiny fake-adapter notebook-equivalent tests locally;
- validate generated notebook JSON;
- create subprocess worker harnesses;
- test archive safety;
- test environment-bootstrap planning;
- test resume logic using fixtures;
- compile the paper;
- generate planning documents;
- regenerate deterministic assets.

## 3.3 Evidence boundary

Use:

```text
planning_only
not_empirical_evidence
claim_allowed=false
```

```text
synthetic_validation_only
not_model_evidence
claim_allowed=false
```

```text
non_evidence_preflight
run_log_only
claim_allowed=false
```

Do not misclassify static validation as successful Kaggle execution.

---

# 4. Required mode of operation

Work in this order:

1. inspect live repository;
2. reproduce current baseline;
3. verify every known defect;
4. repair runtime architecture;
5. repair canonical execution wiring;
6. strengthen local validation;
7. regenerate notebooks and docs;
8. run full local-safe verification;
9. produce one exact final status;
10. produce one exact next command.

For every finding classify:

```text
CONFIRMED
ALREADY_FIXED
PARTIALLY_FIXED
NOT_REPRODUCED
NEW_DEFECT
BLOCKED_BY_REAL_EXECUTION
```

Do not draft the final report before inspecting the implementation.

---

# 5. Phase A — Reproduce the baseline

Run all available local-safe checks:

- Python compilation;
- package imports;
- non-recursive full pytest;
- statistical lane;
- artifact-contract lane;
- CVPR extended synthetic/gate lane;
- notebook static analyzer;
- CVPR final audit;
- forensic audit;
- V9 compatibility audit;
- paper firewall;
- privacy scan;
- release scan;
- Ruff;
- critical mypy lane;
- full mypy for debt comparison;
- paper compilation;
- `git diff --check`.

Record exact:

```text
command
working directory
environment
exit code
duration
passed
failed
skipped
warnings
output
```

Create or update:

```text
reports/CERTGEN_FINAL_HARDENING_BASELINE.md
reports/CERTGEN_FINAL_HARDENING_COMMAND_LEDGER.csv
reports/CERTGEN_FINAL_HARDENING_CURRENT_STATE.json
```

---

# 6. Phase B — Build a real Kaggle environment bootstrap

Create one reusable environment-bootstrap implementation shared by all five canonical notebooks.

Preferred architecture:

```text
certgen/notebooks/environment_bootstrap.py
```

and generated notebook cells that call or inline the same deterministic logic.

## 6.1 Requirements

The bootstrap must:

1. print current Python version;
2. print current pip version;
3. print current relevant package versions;
4. compare installed versions against a frozen compatibility profile;
5. install only missing/incompatible packages;
6. use exact or bounded version pins justified by compatibility;
7. avoid unnecessary reinstall of compatible packages;
8. produce a machine-readable environment report;
9. produce a requirements lock snapshot;
10. detect when a kernel restart is required;
11. provide a clear stop/restart instruction;
12. revalidate versions after restart;
13. remain idempotent across reruns;
14. fail closed when the final environment does not match;
15. avoid hiding installation failures;
16. log installation output;
17. record network requirement;
18. label the output as run-log-only.

## 6.2 Compatibility profiles

Create explicit profiles such as:

```text
kaggle_t4x2_generation
kaggle_t4x2_features
kaggle_t4x2_preflight
```

Do not assume every extractor and generator requires identical dependencies.

## 6.3 Avoid fragile over-pinning

Do not pin every transitive dependency unless necessary.

Pin the compatibility-critical packages and record the final full environment.

## 6.4 Local fixture validation

Add tests that simulate:

- all packages compatible;
- one package missing;
- one incompatible package;
- installation failure;
- restart required;
- offline mode;
- revalidation failure.

No package installation should occur in normal unit tests.

---

# 7. Phase C — Enforce explicit online/offline model asset policy

Introduce a typed policy:

```text
ONLINE_PREFLIGHT_DOWNLOAD
OFFLINE_PACKAGED_CACHE
```

Every checkpoint and feature-extractor run must declare one.

## 7.1 Online preflight mode

When enabled:

- Kaggle internet must be explicitly enabled;
- downloads occur only in checkpoint/extractor preflight;
- model IDs and revisions must be pinned;
- authentication requirement must be checked;
- license status must be recorded;
- download paths must be controlled;
- downloaded file inventory must be recorded;
- hashes must be captured where feasible;
- cache manifest must be produced;
- later generation/feature runs must reuse the validated cache;
- unexpected redownload must be blocked or clearly logged.

## 7.2 Offline packaged-cache mode

When enabled:

- required cache directories must be present in Kaggle input datasets;
- package contents must be validated before import;
- model/config/tokenizer/scheduler/weight files must be checked;
- cache manifest and hash must match the preflight-approved manifest;
- local-files-only mode must be enforced;
- missing assets must fail before GPU allocation.

## 7.3 Asset manifest

Create:

```text
model_asset_manifest.json
```

Fields:

```text
asset_id
model_or_extractor_id
revision
source
license
authentication_required
files
file_hashes
total_size
cache_root
policy
validated_at
validation_status
```

## 7.4 Registry integration

Extend model and feature registries with:

```text
asset_policy
asset_manifest_required
online_preflight_supported
offline_cache_supported
expected_cache_size
```

## 7.5 No fabricated license readiness

Unknown licenses remain blocked or planning-only.

---

# 8. Phase D — Replace forked CUDA workers with isolated subprocess workers

Create a shared subprocess worker architecture.

Preferred structure:

```text
certgen/notebooks/workers/
    generation_worker.py
    feature_worker.py
    preflight_worker.py
certgen/notebooks/subprocess_orchestrator.py
```

## 8.1 GPU isolation requirement

Each worker must be launched like:

```bash
CUDA_VISIBLE_DEVICES=0 python -m certgen.notebooks.workers.generation_worker ...
CUDA_VISIBLE_DEVICES=1 python -m certgen.notebooks.workers.generation_worker ...
```

The worker must set and verify GPU visibility before importing or initializing PyTorch.

## 8.2 Parent process rules

The parent notebook may inspect basic system information but must not initialize CUDA before launching isolated GPU workers.

Do not call:

```python
torch.cuda.*
```

in a way that initializes CUDA before workers launch.

## 8.3 Worker verification

Each worker must emit:

```text
physical GPU assignment
visible GPU count
logical device
GPU name
CUDA version
PyTorch version
worker PID
configuration hash
shard ID
```

## 8.4 Process monitoring

The orchestrator must:

- launch workers independently;
- stream or preserve logs;
- capture exit codes;
- terminate cleanly on failure;
- preserve completed shards;
- mark partial failure honestly;
- generate exact rerun commands.

## 8.5 Static analyzer update

Remove any rule requiring `fork`.

Replace it with checks for:

- subprocess worker isolation;
- `CUDA_VISIBLE_DEVICES`;
- worker entrypoint;
- per-worker status;
- non-overlapping shard assignment;
- parent CUDA non-initialization.

## 8.6 Fixture tests

Use fake workers with no GPU to validate:

- two workers launched;
- correct environment variables;
- one worker failure;
- timeout;
- resume after one completed shard;
- log preservation;
- exit-code propagation.

---

# 9. Phase E — Implement true batched generation

Repair the generation engine so `batch_size` is real.

## 9.1 Batch contract

For each batch:

```text
batch_id
sample_ids
seeds
prompts_or_labels
model_id
scheduler
inference_steps
guidance_scale
precision
device
start_time
end_time
status
```

## 9.2 Deterministic generation

Where supported:

- use per-image `torch.Generator` objects;
- preserve one seed per sample;
- preserve sample order;
- preserve deterministic reruns.

Where the pipeline API cannot support a list of generators:

- fall back to a safe smaller batch;
- or use deterministic microbatches;
- record the fallback.

## 9.3 Adaptive OOM handling

Implement:

1. configured batch size;
2. on OOM, clear worker-local GPU cache;
3. halve batch size;
4. retry the failed batch;
5. continue until minimum batch size;
6. fail honestly if minimum batch size also fails.

Record:

```text
configured_batch_size
effective_batch_size
OOM_events
fallback_reason
```

## 9.4 Atomic writes

Write images and batch manifests to a temporary location.

Only mark the batch complete after:

- every image decodes;
- dimensions match;
- mode matches;
- sample IDs match;
- hashes are written;
- seed uniqueness passes.

## 9.5 Resume

Resume from completed sample IDs, not only shard IDs.

Reject:

- duplicate sample IDs;
- duplicate seeds where forbidden;
- conflicting existing image hashes;
- changed generation configuration.

## 9.6 Throughput calibration

Checkpoint preflight must measure:

```text
seconds per image
images per minute
peak VRAM
effective batch size
```

These are run-log-only.

The runtime planner must support recalculating future estimates using measured preflight throughput.

Do not treat planning estimates as measurements before preflight.

---

# 10. Phase F — Prove actual feature preprocessing

Implement an observed preprocessing contract.

## 10.1 Required fields

For each extractor, capture at runtime:

```text
extractor_id
model_identifier
revision
processor_class
input_resolution
resize_size
crop_size
crop_mode
interpolation
antialias
pixel_range
channel_order
mean
std
feature_normalization
precision
output_dimension
package_versions
```

## 10.2 Expected versus observed

Every feature config must contain a frozen expected preprocessing contract.

Before extraction:

- derive observed preprocessing from the actual processor/model;
- normalize representation;
- compare expected and observed;
- fail closed on mismatch;
- write a difference report.

## 10.3 No unresolved placeholders

A real extraction config must not contain:

```text
TBD
TBD_EXACT
UNKNOWN
```

for any claim-bearing preprocessing field.

Planning templates may contain placeholders but must fail freeze validation.

## 10.4 Processor adapters

Implement extractor-specific adapters for:

- Inception;
- CLIP;
- DINOv2 or selected DINO implementation.

Do not rely only on generic processor serialization.

## 10.5 Feature verification

For a fixture image batch, test:

- deterministic preprocessing;
- deterministic feature shape;
- expected normalization;
- output dimension;
- sample-order preservation;
- batch-size invariance within tolerance.

Fixture adapters may be used in CI.

---

# 11. Phase G — Implement explicit resume, restart, and force-new-run modes

Every canonical notebook must accept:

```text
mode: resume
mode: restart
mode: force_new_run
```

## 11.1 Resume

Allowed only when:

- run ID matches;
- configuration hash matches;
- input manifest hash matches;
- asset manifest hash matches;
- completed shard markers validate;
- prior outputs are not corrupt.

Reuse:

- extracted input package;
- downloaded model cache;
- completed shards;
- valid feature caches;
- logs.

## 11.2 Restart

Restart the current run while preserving prior state under a quarantine/archive path.

Do not overwrite raw copied-back artifacts.

## 11.3 Force new run

Create a new run ID and new output root.

Do not reuse prior completion markers.

## 11.4 Existing final ZIP

If all shards are valid but the final ZIP is missing or corrupt, rebuild only the ZIP.

## 11.5 Quarantine

Move incompatible prior state to:

```text
quarantine/<timestamp>_<reason>/
```

Record the reason and hashes.

## 11.6 Idempotence tests

Validate:

- rerun after input extraction;
- rerun after one shard;
- rerun after all shards;
- rerun after ZIP corruption;
- changed config;
- changed input hash;
- changed asset cache;
- partial logs;
- partial image batch.

---

# 12. Phase H — Canonical configuration builders

Add canonical preparation commands:

```bash
python3 -m certgen prepare preflight
python3 -m certgen prepare generation --scale 1k
python3 -m certgen prepare features
python3 -m certgen prepare family
python3 -m certgen prepare runtime-plan
```

Use the exact CLI conventions already present where possible.

## 12.1 Preflight builder

Inputs:

- model registry;
- feature registry;
- benchmark registry;
- asset policy.

Outputs:

- frozen preflight config;
- input package;
- configuration hash;
- expected output contract;
- Kaggle upload guide.

## 12.2 Generation builder

Inputs:

- validated reference state where required;
- successful preflight import;
- benchmark;
- models;
- scale;
- seeds;
- shard count.

Outputs:

- frozen generation config;
- shard assignments;
- seed ledger;
- input ZIP;
- runtime plan;
- expected output ZIP name.

## 12.3 Feature builder

Inputs:

- imported generation artifact;
- materialized reference;
- feature registry;
- preprocessing contract;
- extractor asset manifests.

Outputs:

- role manifest;
- frozen feature config;
- shard assignments;
- input ZIP;
- expected cache dimensions;
- expected output contract.

## 12.4 Family builder

Inputs:

- validated feature caches;
- preregistration;
- comparison registry;
- alpha;
- feature spaces;
- metrics.

Outputs:

- frozen Bonferroni family registry;
- pair list;
- alpha allocation;
- configuration hash;
- certificate command.

## 12.5 Validation

No builder may freeze a config containing unresolved placeholders.

---

# 13. Phase I — Wire the next-action engine to the canonical CVPR pipeline

The next-action engine must never point a current CVPR run toward legacy V6/V9 scripts unless the canonical command explicitly wraps them.

Create one direct mapping from the CVPR stage state machine to:

```text
canonical CLI command
canonical notebook
canonical config builder
canonical importer
canonical validator
canonical expected output
```

## 13.1 Required stages

At minimum:

```text
REFERENCE_SOURCE_REQUIRED
REFERENCE_VALIDATION_REQUIRED
REFERENCE_MATERIALIZATION_REQUIRED
PREFLIGHT_CONFIG_REQUIRED
KAGGLE_PREFLIGHT_REQUIRED
PREFLIGHT_IMPORT_REQUIRED
GENERATION_CONFIG_REQUIRED
KAGGLE_GENERATION_REQUIRED
GENERATION_IMPORT_REQUIRED
FEATURE_CONFIG_REQUIRED
KAGGLE_FEATURE_EXTRACTION_REQUIRED
FEATURE_IMPORT_REQUIRED
CACHE_VALIDATION_REQUIRED
METRIC_REPRODUCTION_REQUIRED
SANITY_GATES_REQUIRED
FAMILY_FREEZE_REQUIRED
FIRST_PILOT_REQUIRED
PARTIAL_RANKING_REQUIRED
STOP_AND_INTERPRET
```

## 13.2 Exact action format

Every action must include:

```text
status
reason
exact command
notebook path
execution location
input
expected output
success validator
planning runtime
CPU_or_GPU
network policy
evidence class
claim permission
failure recovery
```

## 13.3 Legacy compatibility

Historical wrappers may remain, but must be labeled:

```text
LEGACY_COMPATIBILITY_ONLY
NOT_CANONICAL_GUIDANCE
```

---

# 14. Phase J — Repair recursive tests

Normal pytest must not launch another full pytest.

## 14.1 Preferred design

Mark integration-heavy audits:

```text
recursive_audit
integration_audit
```

Run them explicitly outside the normal suite.

Or refactor tests to call the audit module directly without spawning pytest.

## 14.2 Required commands

Document:

```bash
pytest -m "not integration_audit"
pytest -m integration_audit
```

The default CI lane should be non-recursive.

## 14.3 Preserve reported totals honestly

Do not inflate test count by counting nested suite execution.

Report:

- unit/fast count;
- integration audit count;
- statistical lane count;
- artifact lane count;
- total unique tests.

---

# 15. Phase K — Stale documentation repair

Audit all current user-facing docs for:

- ADE20K references;
- old V6 commands;
- old V9 notebook names;
- stale statuses;
- outdated benchmark plans;
- absolute private paths;
- unsupported metric-agnostic language;
- old test counts;
- old runtime estimates;
- old archive claims.

## 15.1 Historical docs

Do not delete historical files.

Add a clear banner:

```text
LEGACY DOCUMENT
SUPERSEDED BY THE CURRENT CVPR EXECUTION HANDBOOK
NOT CANONICAL EXECUTION GUIDANCE
```

## 15.2 Canonical guidance

The only canonical execution source should be:

```text
CERTGEN_CVPR_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md
```

Ensure all README and next-action links point to it.

## 15.3 ADE20K

Regenerate the repository safety inventory so it correctly states that ADE20K data/root was intentionally removed for space and is irrelevant to the active CertGen pipeline.

---

# 16. Phase L — Clean archive and reproducibility export

Create a canonical export tool:

```bash
python3 -m certgen release build-archive
```

or an equivalent repository script.

## 16.1 Exclusions

Exclude:

```text
.git/
__MACOSX/
.DS_Store
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
large local datasets
raw private caches
temporary notebooks
quarantine/
```

## 16.2 Required root files

Include when present:

```text
README.md
LICENSE
CITATION.cff
pyproject.toml
.gitignore
Makefile
core package
tests
configs
canonical notebooks
canonical docs
paper sources
release manifest
```

## 16.3 Path preservation

Preserve canonical paths such as:

```text
notebooks/kaggle/
```

Do not flatten notebooks into a root `kaggle/` directory.

## 16.4 Archive verification

After archive creation:

- extract to a temporary directory;
- run import checks;
- run non-Git tests;
- validate notebook paths;
- validate required files;
- validate no forbidden metadata;
- generate archive hash;
- generate archive manifest.

## 16.5 Git-aware tests

Tests requiring `.git` or `git check-ignore` must skip cleanly or use fixture repositories in portable archives.

---

# 17. Phase M — Additional high-value CVPR readiness upgrades

Only implement these if they are tightly integrated and locally testable.

## 17.1 Smoke-throughput calibration mode

Add a non-evidence smoke mode that runs only during real checkpoint preflight:

```text
4–16 images
measured throughput
peak VRAM
effective batch size
download/cache time
```

The runtime planner should ingest this report.

## 17.2 Model adapter capability matrix

Create a machine-readable adapter capability registry:

```text
supports_batching
supports_generator_list
supports_class_conditioning
supports_prompt_batching
supports_scheduler_override
supports_mixed_precision
supports_resume
known_memory_risk
```

This prevents generic generation logic from assuming every model behaves the same.

## 17.3 Extractor memory calibration

Feature preflight should test a small sequence of batch sizes and choose the largest safe batch size.

Record:

```text
tested batch sizes
peak VRAM
selected batch size
fallback batch size
```

## 17.4 Disk guard

Before each stage:

- estimate required disk;
- compare with free disk;
- reserve safety margin;
- fail before expensive work if insufficient.

## 17.5 Checkpoint-cache completeness validator

Validate offline caches without loading full GPU models.

Check:

- expected files;
- config;
- tokenizer;
- scheduler;
- weights;
- revision manifest;
- size;
- hashes.

## 17.6 Runtime contract test harness

Create a local fake-adapter harness that executes the same subprocess, batching, resume, merge, ZIP, and import path using tiny synthetic images/features.

This is more valuable than notebook text checks alone.

Required end-to-end fixture stages:

```text
fake preflight
fake generation on two logical workers
fake generation resume
fake feature extraction
fake import
fake cache validation
fake metric gate
fake certificate
fake partial ranking
```

Label everything synthetic-only.

## 17.7 Failure injection

Test:

- worker crash;
- OOM simulation;
- corrupt image;
- duplicate seed;
- missing shard;
- mismatched preprocessing;
- wrong model revision;
- corrupt output ZIP;
- changed config on resume;
- missing cache asset;
- insufficient disk.

## 17.8 Reproducibility fingerprint

Create a single fingerprint object combining:

```text
benchmark registry hash
model registry hash
feature registry hash
preregistration hash
reference manifest hash
asset manifest hash
generation config hash
feature config hash
family config hash
code commit when available
environment hash
```

All claim-bearing outputs must record this fingerprint.

---

# 18. Phase N — Notebook regeneration

Regenerate all five canonical notebooks from one deterministic source builder.

Expected canonical notebooks include:

```text
notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb
notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb
```

## 18.1 Required notebook structure

Each notebook must include:

1. title and evidence label;
2. run contract summary;
3. environment bootstrap;
4. input discovery;
5. input hash/config validation;
6. network/cache policy validation;
7. disk check;
8. GPU visibility without parent CUDA initialization;
9. worker-script preparation;
10. subprocess launch;
11. per-worker monitoring;
12. resume/restart handling;
13. shard validation;
14. deterministic merge;
15. integrity manifest;
16. deterministic output ZIP;
17. copy-back instructions;
18. exact local import command;
19. failure recovery instructions;
20. final status summary.

## 18.2 Static analyzer requirements

The analyzer must validate all of the above structurally.

It must also ensure:

```text
no forked CUDA multiprocessing
no parent torch CUDA initialization
no certificate generation
no paper evidence
no claim_allowed=true
no secrets
no absolute private paths
```

## 18.3 Notebook terminology

Never label notebooks:

```text
errorless
fully verified
production proven
```

before real Kaggle execution.

Allowed:

```text
production-hardened
static-validation passed
fixture-runtime passed
real Kaggle preflight required
```

---

# 19. Phase O — Update the runtime planner

The runtime planner must support:

- planning estimates;
- preflight-measured throughput;
- effective batch size;
- model-specific throughput;
- feature-extractor throughput;
- download/cache time;
- shard count;
- session count;
- disk;
- RAM;
- VRAM;
- ZIP size;
- copy-back checkpoints.

## 19.1 Planning versus measured

Every output field must be tagged:

```text
planning_estimate
measured_preflight
derived_from_measured_preflight
```

## 19.2 Session plan

For each Kaggle run produce:

```text
session_id
models
shards
expected duration
expected output checkpoint
resume command
copy-back ZIP
```

## 19.3 Post-preflight recalculation

Add:

```bash
python3 -m certgen runtime-plan \
  --ingest-preflight <preflight_report>
```

or equivalent.

---

# 20. Phase P — Final end-to-end synthetic runtime test

Build one local end-to-end synthetic workflow that uses the same canonical CLI and artifact contracts as the real pipeline.

It must exercise:

1. synthetic reference materialization;
2. fake checkpoint preflight;
3. two-worker fake generation;
4. generation resume;
5. fake feature extraction;
6. feature merge;
7. secure ZIP import;
8. cache-v2 validation;
9. metric reproduction gate;
10. null and obvious-gap sanity gates;
11. frozen Bonferroni family;
12. certificate output;
13. partial ranking;
14. figure-contract approval denial;
15. paper firewall denial;
16. final non-evidence audit.

The workflow must finish with:

```text
synthetic_validation_only
claim_allowed=false
```

This is not empirical evidence.

---

# 21. Phase Q — Final verification

After all repairs, run:

```text
Python compilation
package imports
non-recursive default tests
integration audit lane
statistical lane
artifact-contract lane
CVPR synthetic/gate lane
new runtime-contract lane
end-to-end synthetic runtime
notebook static analyzer
notebook deterministic regeneration check
registry/schema validation
CLI smoke tests
environment-bootstrap fixture tests
subprocess-worker fixture tests
batch/resume tests
asset-policy tests
archive export test
paper firewall
privacy scan
release scan
Ruff
critical mypy
full mypy debt comparison
paper compilation
git diff --check
CVPR final audit
forensic audit
V9 compatibility audit
```

No local test should:

- access the network;
- download real models;
- require CUDA;
- require CIFAR;
- create real paper evidence.

---

# 22. Final status taxonomy

Choose exactly one:

```text
FINAL_HARDENING_FAILED
FINAL_HARDENING_PARTIAL_TESTS_FAILING
FINAL_HARDENING_BLOCKED_BY_LOCAL_DEFECT
CVPR_RUNTIME_HARDENED_BLOCKED_BY_REFERENCE_INPUT
CVPR_REFERENCE_READY_PREFLIGHT_REQUIRED
CVPR_REAL_PREFLIGHT_REQUIRED
CVPR_1K_GENERATION_READY
```

Expected likely result:

```text
CVPR_RUNTIME_HARDENED_BLOCKED_BY_REFERENCE_INPUT
```

Do not force it.

Report sub-statuses for:

```text
environment bootstrap
asset policy
GPU isolation
batch generation
preprocessing proof
resume/restart
config builders
next-action wiring
test architecture
archive export
reference
preflight
generation
features
metric gates
certificate
partial ranking
paper
```

---

# 23. Required final artifacts

Create:

```text
CERTGEN_CVPR_FINAL_RUNTIME_HARDENING_REPORT.md
CERTGEN_CVPR_FINAL_EXECUTION_HANDBOOK.md

reports/CERTGEN_FINAL_HARDENING_BASELINE.md
reports/CERTGEN_FINAL_HARDENING_COMMAND_LEDGER.csv
reports/CERTGEN_FINAL_HARDENING_CURRENT_STATE.json
reports/CERTGEN_FINAL_HARDENING_REPAIR_CHANGELOG.md
reports/CERTGEN_FINAL_HARDENING_TEST_MATRIX.md
reports/CERTGEN_FINAL_HARDENING_NOTEBOOK_READINESS.md
reports/CERTGEN_FINAL_HARDENING_ARCHIVE_AUDIT.md

docs/execution/CERTGEN_KAGGLE_ENVIRONMENT_BOOTSTRAP.md
docs/execution/CERTGEN_MODEL_ASSET_POLICY.md
docs/execution/CERTGEN_T4X2_SUBPROCESS_ARCHITECTURE.md
docs/execution/CERTGEN_BATCH_AND_OOM_PROTOCOL.md
docs/execution/CERTGEN_PREPROCESSING_OBSERVED_CONTRACT.md
docs/execution/CERTGEN_RESUME_RESTART_FORCE_PROTOCOL.md
docs/execution/CERTGEN_CANONICAL_PREPARE_COMMANDS.md
docs/execution/CERTGEN_RUNTIME_CALIBRATION_PROTOCOL.md
docs/execution/CERTGEN_CLEAN_ARCHIVE_GUIDE.md

docs/CERTGEN_CVPR_EXACT_NEXT_ACTION.md
docs/CERTGEN_CVPR_SINGLE_FILE_HANDOFF.md
```

Update the existing canonical CVPR handbook rather than leaving two conflicting handbooks.

If a new final handbook is created, mark the previous one as superseded.

---

# 24. Required final report structure

`CERTGEN_CVPR_FINAL_RUNTIME_HARDENING_REPORT.md` must include:

## 1. Executive verdict

State:

- whether all known runtime leaks were fixed;
- whether new defects were found;
- whether notebooks are production-hardened;
- whether real Kaggle validation is still required;
- exact blocker;
- exact next command;
- whether any further pre-run patch is justified.

## 2. Baseline reproduction

- test counts;
- audit counts;
- mypy;
- paper;
- git state;
- archive state.

## 3. Known findings

For each of the 11 known defects:

```text
status
root cause
repair
files changed
tests
remaining risk
```

## 4. New value upgrades

- bootstrap;
- asset policy;
- subprocess workers;
- batching;
- OOM handling;
- preprocessing proof;
- config builders;
- runtime calibration;
- fake end-to-end runtime;
- archive export;
- reproducibility fingerprint.

## 5. Notebook readiness matrix

For each notebook:

```text
environment bootstrap
network policy
offline cache support
GPU isolation
batching
resume
OOM handling
preprocessing proof
integrity manifest
output ZIP
fixture runtime
static analyzer
real Kaggle tested
known risk
```

## 6. Verification

Exact commands and exit codes.

## 7. Remaining blockers

Separate:

```text
USER_INPUT
REAL_KAGGLE_RUNTIME
REAL_MODEL_LOAD
REAL_GENERATION
REAL_FEATURES
REAL_METRIC_REPRODUCTION
REAL_CERTIFICATE
REAL_CVPR_EVIDENCE
```

## 8. Stop-building verdict

Explicitly state whether more pre-run infrastructure is justified.

The desired conclusion, only if earned:

> No further broad pre-execution upgrades are justified. The project must now execute the reference validation and real Kaggle checkpoint preflight.

## 9. Exact next action

One command.

---

# 25. Final execution handbook requirements

The updated canonical handbook must include:

- exact reference-source placement;
- exact validation command;
- materialization;
- preflight config preparation;
- Kaggle internet/offline-cache decision;
- preflight notebook;
- copy-back;
- import;
- measured runtime recalculation;
- generation config preparation;
- generation notebook;
- feature config preparation;
- feature notebook;
- cache validation;
- metric gates;
- sanity gates;
- family freeze;
- certificate;
- partial ranking;
- stop-and-interpret gate.

For every step include:

```text
location
CPU_or_GPU
GPU count
network policy
input
output
command/notebook
planning runtime
measured runtime field
disk
RAM
VRAM
resume behavior
failure recovery
evidence class
claim permission
completion test
```

---

# 26. Priorities

Classify all work as:

```text
P0 — runtime correctness or evidence integrity
P1 — required before first Kaggle preflight
P2 — required before 1k generation
P3 — required before feature extraction
P4 — CVPR value upgrade
P5 — optional post-pilot
REJECTED — overengineering
```

Do not add unrelated theory, metrics, dashboards, web apps, or paper prose.

---

# 27. Stop-building rule

After this pass, stop all broad pre-execution development.

Only patch further if:

- the real checkpoint preflight fails;
- the environment bootstrap fails on Kaggle;
- a model adapter fails;
- T4×2 isolation fails;
- OOM handling fails;
- preprocessing proof fails;
- copied-back output fails validation;
- real metric reproduction fails;
- a real evidence gate finds a defect.

Do not create another general upgrade prompt.

Do not build before the first pilot:

- e-BH extensions;
- rigorous FID certificates;
- full video pipeline;
- arbitrary model plugin systems;
- cloud orchestration;
- dashboards;
- web interfaces;
- automatic manuscript generation;
- more historical migration layers.

---

# 28. Completion condition

This task is complete only when:

1. baseline is reproduced;
2. all known defects are classified;
3. environment bootstrap exists;
4. asset policy is explicit and enforced;
5. CUDA workers use isolated subprocesses;
6. generation batching is real;
7. OOM fallback exists;
8. observed preprocessing is verified;
9. resume/restart/force modes work;
10. canonical config builders exist;
11. next-action engine is fully CVPR-native;
12. recursive tests are repaired;
13. stale ADE20K and legacy guidance are corrected;
14. clean archive export exists;
15. all five notebooks are regenerated;
16. static validation passes;
17. fixture-runtime validation passes;
18. end-to-end synthetic runtime passes;
19. all local-safe tests and audits pass;
20. exact final status is reported;
21. one exact next command is reported;
22. the report explicitly states whether any further pre-run patch is warranted.

Begin now by inspecting the live repository and reproducing the baseline. Do not write the final verdict before examining the code and running the local-safe checks.
