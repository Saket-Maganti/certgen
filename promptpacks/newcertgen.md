# CERTGEN — FINAL REAL-EXECUTION CLOSURE, KAGGLE HANDOFF REPAIR, MODEL/FEATURE PREFLIGHT COMPLETION, AND RUN-READY SEAL

You are GPT-5.6 Sol operating as:

* a senior computer-vision researcher;
* a generative-model evaluation researcher;
* a sequential-inference specialist;
* a research software architect;
* a Kaggle T4×2 execution engineer;
* a reproducibility and artifact-integrity auditor;
* a CVPR reviewer focused on whether the repository can actually produce trustworthy results.

You have full access to the live repository:

```text
/Users/saketmaganti/Projects/certGen
```

Your task is to perform the **final real-execution closure pass** for CertGen.

This is not another broad architecture upgrade.

This is not a new version layer.

Do not create V10/V11/V12 prompt packs or parallel execution systems.

Work directly on the canonical CVPR pipeline and repair the exact runtime handoff defects that still prevent a continuous real execution from:

```text
validated reference
→ real checkpoint/extractor preflight
→ Kaggle T4×2 generation
→ local import
→ Kaggle T4×2 feature extraction
→ local feature merge/cache-v2
→ metric reproduction
→ sanity gates
→ frozen Bonferroni family
→ first certificate pilot
→ certified partial ranking
```

The end state must be:

> The repository is locally and contractually ready to begin the real CIFAR reference validation and the first Kaggle preflight, with no known broken handoff, missing builder, schema mismatch, or runtime path discontinuity remaining.

The project still must not run real datasets, checkpoints, generation, features, metrics, certificates, or paper evidence during this pass.

---

# 1. Current verified state

The previous hardening work produced substantial real improvements:

* 241 default tests reportedly passed;
* four integration audits reportedly passed;
* 31 statistical tests passed;
* 25 artifact-contract tests passed;
* five canonical notebooks passed static and fixture-runtime validation;
* CVPR audit passed 8/8;
* forensic audit passed 8/8;
* V9 compatibility passed 22/22;
* critical mypy passed;
* full-tree historical mypy debt remained unchanged;
* a clean reproducibility archive was created;
* no real data, checkpoint, Kaggle, generation, feature, metric, certificate, or paper evidence was fabricated;
* `claim_allowed=false` was preserved.

The live repository is the source of truth. Reproduce or correct every claim.

The current scientific core remains:

* bounded RBF-MMD difference stream;
* direct pairwise contributions;
* non-overlapping sample units;
* conservative support bounds;
* union-Hoeffding time-uniform confidence sequence;
* first-crossing directional decision;
* Bonferroni family-wise control;
* FID/FD descriptive unless separately justified;
* polynomial KID not automatically certified;
* evidence firewall fail-closed.

Do not expand the statistical claim surface in this pass.

---

# 2. Current honest state

The previous status:

```text
CVPR_RUNTIME_HARDENED_BLOCKED_BY_REFERENCE_INPUT
```

is too optimistic.

The honest current state is:

```text
CVPR_RUNTIME_HARDENING_PARTIAL
CORE_AND_SYNTHETIC_CONTRACTS_STRONG
REAL_EXECUTION_PATH_INCOMPLETE
BLOCKED_BY_REFERENCE_INPUT_AND_RUNTIME_INTEGRATION_DEFECTS
```

This pass must repair the incomplete real path.

The expected final status, only if earned, is:

```text
CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT
```

---

# 3. Confirmed defects that must be repaired

Treat the following as confirmed unless the live repository proves they have already been fixed.

## 3.1 Checkpoint preflight does not actually load checkpoints

Current preflight may:

* download or validate cache;
* inventory files;
* write an asset manifest;
* record hardware.

It may not:

* instantiate the actual model pipeline;
* load model weights into CPU/GPU memory;
* validate scheduler compatibility;
* generate 1–4 smoke images;
* decode and validate them;
* measure throughput;
* measure peak VRAM;
* validate model-family-specific sampling semantics.

A preflight that only checks files must never return:

```text
PREFLIGHT_PASS
```

It should return something like:

```text
ASSET_CACHE_VALID
REAL_MODEL_LOAD_NOT_RUN
```

until real loading and smoke generation succeed.

## 3.2 T4×2 scheduler launches too many processes per GPU

The orchestrator may assign multiple model workers to GPU 0 and GPU 1 and launch them all simultaneously.

This can produce:

* multiple large model loads on one T4;
* immediate OOM;
* invalid throughput;
* unstable scheduler behavior.

The runtime must enforce:

```text
maximum active GPU workers per physical GPU = 1
```

unless a specific lightweight adapter explicitly declares safe concurrency.

## 3.3 Generic Diffusers adapter ignores frozen generation parameters

The real generation adapter may not reliably apply:

* batch size;
* number of inference steps;
* scheduler choice;
* guidance scale;
* width;
* height;
* class conditioning;
* prompt conditioning;
* generator-list semantics;
* precision.

The config may record these values while the actual model call ignores them.

## 3.4 Unsupported CFM adapter is promoted into the generic path

The adapter registry may mark a CFM model as:

```text
blocked_real_adapter_preflight_required
supports_batching: false
supports_generator_list: false
```

but the generation preparation path may override this with optimistic generic capability flags.

Unsupported or unverified adapters must remain blocked.

## 3.5 Offline cache layout is inconsistent with runtime loading

Preflight may download to a direct snapshot directory using `snapshot_download(local_dir=...)`.

Generation or feature loading may later call:

```python
from_pretrained(repo_id, cache_dir=cache_root, local_files_only=True)
```

which may not resolve the direct local snapshot.

The runtime must load the exact validated local path.

This affects:

* Diffusers checkpoints;
* CLIP;
* DINO;
* Inception/Torchvision weights.

## 3.6 Dependency network and model-asset network are conflated

Generation and feature configs may disable all network because assets are expected offline.

This also prevents pip/dependency repair in a fresh Kaggle image.

The runtime needs separate controls:

```text
dependency_network_allowed
model_asset_network_allowed
```

or an explicit offline wheelhouse.

## 3.7 `prepare features` is incomplete

The canonical feature preparation path may end in `NotImplementedError`.

The feature stage must be able to build a complete frozen real-run package from:

* imported generated samples;
* materialized reference;
* feature registry;
* extractor asset manifests;
* observed preprocessing contracts;
* deterministic image-role shards.

## 3.8 `prepare family` uses the wrong registry field

The family builder may read:

```text
prospective_status
```

while the comparison registry contains:

```text
prospective_or_posthoc
status
```

This can prevent every real comparison from entering the family.

## 3.9 Notebook output ZIP schema and importer allowlist disagree

The notebooks may package paths such as:

```text
run_identity.json
model_cache/
per_asset/
orchestration/
merge_index.json
status/run_state.json
```

while the importer rejects them as unknown.

The notebook and importer must share one formal output schema.

## 3.10 Preflight-to-generation handoff is incomplete

`prepare generation` may create only:

* generation config;
* seed ledger.

It may fail to package:

* preflight status;
* asset manifests;
* model caches;
* model-ID mappings;
* runtime calibration;
* expected output contract.

## 3.11 Feature extraction produces shards but no merged cache-v2 artifact

Feature workers may emit per-shard outputs and a merge index without actually producing:

* deterministic merged features;
* per-role/per-model arrays;
* final sidecars;
* sample-order manifests;
* cache-v2 lineage;
* validation-ready merged paths.

## 3.12 Feature extractor preflight is missing

The checkpoint preflight path may inspect only generative models and not:

* CLIP;
* DINO;
* Inception;
* tokenizer/processor assets;
* observed preprocessing;
* safe feature batch sizes;
* feature output dimensions.

## 3.13 Resume validation trusts marker existence

The orchestrator may treat a worker as complete when a completion marker file exists without checking:

* status;
* config hash;
* input hash;
* asset hash;
* output hashes;
* output existence;
* schema.

## 3.14 Final ZIP reruns are not idempotent

The notebook may refuse to rebuild or reuse a valid final ZIP and may fail when:

* the ZIP already exists;
* the ZIP is corrupt;
* all shards are valid but the ZIP is missing;
* restart uses the same run ID.

## 3.15 Portable archive does not fully reproduce the declared suite

Potential issues include:

* archive-audit report omitted from the archive;
* tests requiring `.git`;
* missing `LICENSE`;
* missing `CITATION.cff`;
* portable test behavior not aligned with the clean archive.

---

# 4. Non-negotiable restrictions

Do not:

* download real datasets locally;
* download large real models during local validation;
* run Kaggle;
* run Colab;
* run real checkpoint loads;
* run real GPU generation;
* run real feature extraction;
* run real metric reproduction;
* run real certificates;
* create empirical figures;
* populate paper result tables;
* set `claim_allowed=true`;
* fabricate availability, license, runtime, or success;
* silently promote unsupported adapters.

Allowed:

* local CPU tests;
* fake adapters;
* synthetic images and features;
* fixture caches;
* worker subprocess tests;
* notebook generation;
* notebook static analysis;
* archive building;
* paper compilation;
* synthetic end-to-end execution;
* schema and contract validation.

All synthetic outputs must remain:

```text
synthetic_validation_only
not_model_evidence
claim_allowed=false
```

---

# 5. Required mode of operation

Work in this order:

1. inspect the live repository;
2. reproduce the reported baseline;
3. verify every defect;
4. repair real checkpoint and extractor preflight;
5. repair GPU queue scheduling;
6. repair model-family-specific generation;
7. repair asset-loading paths;
8. repair network policy;
9. complete all prepare/package/import/merge handoffs;
10. repair resume and final-ZIP idempotence;
11. repair portable release behavior;
12. run an end-to-end synthetic pipeline using the exact real contracts;
13. run the full local-safe validation matrix;
14. produce one exact final status;
15. produce one exact next action.

For each defect classify:

```text
CONFIRMED
ALREADY_FIXED
PARTIALLY_FIXED
NOT_REPRODUCED
NEW_DEFECT
BLOCKED_BY_REAL_KAGGLE_VALIDATION
```

---

# 6. Phase A — Baseline reproduction

Run:

* Python compilation;
* package imports;
* default non-recursive pytest;
* integration-audit lane;
* statistical lane;
* artifact-contract lane;
* CVPR runtime-hardening lane;
* end-to-end synthetic runtime;
* notebook static analyzer;
* deterministic notebook regeneration;
* CVPR final audit;
* forensic audit;
* V9 compatibility audit;
* paper firewall;
* privacy scan;
* release scan;
* Ruff;
* critical mypy;
* full mypy debt comparison;
* paper compilation;
* `git diff --check`.

Record:

```text
command
cwd
environment
start
end
duration
exit_code
passed
failed
skipped
warnings
output
```

Create or update:

```text
reports/CERTGEN_REAL_EXECUTION_CLOSURE_BASELINE.md
reports/CERTGEN_REAL_EXECUTION_CLOSURE_COMMAND_LEDGER.csv
reports/CERTGEN_REAL_EXECUTION_CLOSURE_CURRENT_STATE.json
```

---

# 7. Phase B — Real checkpoint preflight

Build a real model-load preflight path.

## 7.1 Required preflight states

Use distinct statuses:

```text
ASSET_CACHE_VALID
MODEL_LOAD_PASS
SMOKE_GENERATION_PASS
PREFLIGHT_PASS
PREFLIGHT_FAIL
```

`PREFLIGHT_PASS` is allowed only after all prior stages pass.

## 7.2 Real model load

The preflight worker must:

1. resolve the validated local asset path;
2. load the correct model-family adapter;
3. load config/tokenizer/scheduler where applicable;
4. instantiate the pipeline;
5. move to the assigned GPU;
6. validate precision;
7. validate scheduler compatibility;
8. validate model revision;
9. generate 1–4 smoke samples;
10. decode every sample;
11. verify shape, dimensions, mode, and range;
12. hash smoke images;
13. measure wall time;
14. measure effective batch size;
15. measure peak VRAM where possible;
16. unload the model;
17. clear worker-local GPU state;
18. emit a structured report.

## 7.3 Smoke output

Produce:

```text
per_model/<model_id>/
    status.json
    model_load.json
    scheduler.json
    smoke_manifest.json
    smoke_images/
    throughput.json
    memory.json
    logs/
```

Evidence label:

```text
non_evidence_preflight
run_log_only
claim_allowed=false
```

## 7.4 Model adapter contract

Create a typed adapter interface:

```text
load()
validate_config()
generate_smoke()
generate_batch()
unload()
capabilities()
```

Adapter capability fields:

```text
supports_batching
supports_generator_list
supports_class_conditioning
supports_prompt_conditioning
supports_guidance
supports_scheduler_override
supports_resolution_override
supports_mixed_precision
supports_cpu_load
supports_gpu_load
known_limitations
```

## 7.5 Unsupported adapters

If a model has no validated adapter, fail before packaging generation.

Do not route it through a generic Diffusers adapter merely because its repository is loadable.

---

# 8. Phase C — Real feature-extractor preflight

Build extractor preflight for:

* Inception;
* CLIP;
* DINOv2 or the selected DINO implementation.

## 8.1 Required checks

For each extractor:

1. validate local asset/cache;
2. load processor/model;
3. capture observed preprocessing;
4. compare expected versus observed preprocessing;
5. run a tiny fixture image batch;
6. validate output dimension;
7. validate finite features;
8. test candidate batch sizes;
9. record peak VRAM;
10. select safe batch size;
11. record effective preprocessing contract;
12. record extractor revision;
13. unload cleanly.

## 8.2 Statuses

```text
EXTRACTOR_ASSET_VALID
EXTRACTOR_LOAD_PASS
PREPROCESSING_MATCH_PASS
FEATURE_SMOKE_PASS
EXTRACTOR_PREFLIGHT_PASS
EXTRACTOR_PREFLIGHT_FAIL
```

## 8.3 Feature registry update

Only mark an extractor operational after imported real preflight proves:

* exact revision;
* exact processor;
* exact preprocessing;
* output dimension;
* safe batch size;
* cache manifest.

---

# 9. Phase D — Per-GPU execution queues

Replace bulk simultaneous launch with per-GPU queues.

## 9.1 Scheduling rule

Default:

```text
one active GPU worker per physical GPU
```

Use two queues:

```text
GPU 0 queue
GPU 1 queue
```

Each queue launches the next worker only after the current worker exits and validates.

## 9.2 Optional concurrency

Allow more than one worker per GPU only when:

* adapter explicitly declares lightweight concurrency;
* memory calibration supports it;
* config explicitly enables it;
* the run is non-default.

## 9.3 Orchestrator output

Emit:

```text
queue_assignments.json
worker_schedule.json
worker_start_end.csv
gpu_utilization_summary.json
worker_exit_codes.json
```

## 9.4 Failure behavior

On worker failure:

* preserve successful workers;
* stop launching dependent workers;
* optionally continue independent workers on the other GPU;
* mark run partial;
* provide exact rerun subset.

## 9.5 Fixture tests

Test:

* three jobs per GPU;
* exactly one active process per GPU;
* one worker crash;
* one GPU queue completes early;
* resume after partial completion;
* timeout;
* queue cancellation;
* deterministic assignment.

---

# 10. Phase E — Model-family-specific generation adapters

Do not use one generic call for every model.

## 10.1 Adapter families

At minimum implement or explicitly support:

* unconditional DDPM;
* conditional diffusion;
* generic Diffusers text-to-image;
* class-conditional Diffusers;
* custom/CFM adapter only if real loading semantics are known.

## 10.2 Config-to-call mapping

Every adapter must map and verify:

```text
batch_size
seeds
num_inference_steps
scheduler
guidance_scale
width
height
prompts
class_ids
precision
output_type
```

## 10.3 Applied configuration record

After pipeline construction, emit:

```text
requested_config
applied_config
differences
adapter_name
pipeline_class
scheduler_class
```

Fail if a claim-relevant requested field cannot be applied.

## 10.4 Batching

For each adapter:

* use real batches;
* use per-sample generators when supported;
* preserve seed-to-sample mapping;
* preserve deterministic sample IDs;
* use safe microbatch fallback if generator lists are unsupported;
* record actual effective batch size.

## 10.5 CFM rule

The CFM model must remain excluded unless:

* a real adapter exists;
* real preflight passes;
* batching/generator semantics are documented;
* scheduler/sampler semantics are frozen.

---

# 11. Phase F — Canonical local asset paths

Unify asset loading.

## 11.1 Asset manifest must record

```text
asset_root
snapshot_path
source_repo
revision
files
hashes
layout_type
loader_type
```

## 11.2 Loader behavior

For direct local snapshots use:

```python
from_pretrained(local_snapshot_path, local_files_only=True)
```

Do not pass the remote repository ID with a direct snapshot root unless the exact Hugging Face cache layout is present.

## 11.3 Per-library loaders

Implement explicit adapters for:

* Diffusers local snapshots;
* Transformers local snapshots;
* Torchvision Inception weights;
* timm/open-clip assets if used.

## 11.4 Cache completeness

Validate required files before GPU load.

---

# 12. Phase G — Separate dependency and asset network policies

Use:

```text
dependency_network_allowed
model_asset_network_allowed
```

## 12.1 Dependency policy

Controls:

* pip install;
* package index access;
* wheelhouse use.

## 12.2 Asset policy

Controls:

* Hugging Face model downloads;
* Torch Hub downloads;
* model weight downloads;
* tokenizer/config downloads.

## 12.3 Supported modes

```text
ONLINE_DEPENDENCIES_ONLINE_ASSETS
ONLINE_DEPENDENCIES_OFFLINE_ASSETS
OFFLINE_DEPENDENCIES_OFFLINE_ASSETS
```

The second mode should be the normal generation/feature path after preflight.

## 12.4 Wheelhouse support

Optionally support a packaged wheelhouse for fully offline reruns.

Do not make it mandatory if it adds unnecessary complexity.

---

# 13. Phase H — Complete `prepare preflight`

The preflight builder must include both:

* generative models;
* feature extractors.

## 13.1 Inputs

* model registry;
* adapter capability registry;
* feature registry;
* benchmark registry;
* dependency profile;
* asset policy;
* revisions;
* license status.

## 13.2 Output package

Create a deterministic ZIP containing:

```text
preflight_config.yaml
models.yaml
extractors.yaml
adapter_capabilities.yaml
dependency_profile.yaml
expected_output_schema.json
worker_configs/
run_identity.json
KAGGLE_INSTRUCTIONS.md
```

Do not include large real assets unless offline mode is selected.

---

# 14. Phase I — Complete `prepare generation`

The generation builder must consume imported real preflight artifacts.

## 14.1 Required inputs

* successful model preflight status;
* model load report;
* smoke generation report;
* adapter capability snapshot;
* asset manifests;
* local asset cache roots or packaged cache references;
* throughput calibration;
* benchmark;
* scale;
* seed plan.

## 14.2 Required output package

Create:

```text
generation_config.yaml
seed_ledger.json
model_runtime_configs/
asset_manifests/
model_cache/ or cache_mount_manifest.json
preflight_status/
runtime_calibration.json
expected_output_schema.json
run_identity.json
KAGGLE_INSTRUCTIONS.md
```

## 14.3 Model-ID mapping

Use one canonical mapping across:

* registry model ID;
* asset ID;
* cache directory;
* output directory;
* certificate model ID.

## 14.4 Block unsupported models

Reject generation packaging if any selected model lacks:

* `PREFLIGHT_PASS`;
* validated adapter;
* asset manifest;
* runtime config;
* smoke output validation.

---

# 15. Phase J — Complete `prepare features`

Remove `NotImplementedError`.

## 15.1 Required inputs

* imported generation artifact;
* materialized reference;
* reference draw plan;
* successful extractor preflight;
* extractor asset manifests;
* observed preprocessing contracts;
* feature registry;
* benchmark;
* model/image role manifests.

## 15.2 Build role manifests

Create deterministic roles:

```text
reference
model_a
model_b
additional_model_roles
```

Each image must have:

```text
sample_id
role
model_id
source_path
image_hash
reference_draw_position where applicable
```

## 15.3 Build deterministic shards

Shard by stable sample IDs.

No duplicate IDs.

No role mixing.

## 15.4 Output package

Create:

```text
feature_config.yaml
role_manifest.csv
reference_draw_plan.json
extractor_configs/
asset_manifests/
preprocessing_contracts/
image_shards/
expected_output_schema.json
run_identity.json
KAGGLE_INSTRUCTIONS.md
```

## 15.5 Freeze validation

Reject unresolved:

```text
TBD
UNKNOWN
UNVERIFIED
```

in any claim-bearing field.

---

# 16. Phase K — Complete feature merge into cache-v2

After feature ZIP import, create a canonical local merge command:

```bash
python3 -m certgen merge features --run <run_id>
```

or equivalent.

## 16.1 Merge behavior

* load all feature shards;
* validate shard schemas;
* validate extractor identity;
* validate preprocessing hash;
* validate source manifest;
* reject duplicate sample IDs;
* reject missing sample IDs;
* sort deterministically by sample ID;
* preserve role/model grouping;
* write atomic merged arrays;
* write final sidecars;
* write completion marker;
* register artifacts.

## 16.2 Cache-v2 outputs

Produce:

```text
data/features/cvpr/<run_id>/<feature_space>/<role>/features.npz
data/features/cvpr/<run_id>/<feature_space>/<role>/sidecar.json
data/features/cvpr/<run_id>/merge_manifest.json
data/features/cvpr/<run_id>/status.json
```

## 16.3 Validation

The next-action engine must not proceed until cache-v2 validation passes.

---

# 17. Phase L — Unify output schemas and importers

Create one shared schema source for:

* preflight ZIP;
* generation ZIP;
* feature ZIP.

Preferred:

```text
certgen/cvpr/output_schemas.py
```

or JSON schemas under:

```text
schemas/cvpr/
```

## 17.1 Schema ownership

The same schema must drive:

* notebook packaging;
* static analyzer;
* importer allowlist;
* archive fixture tests;
* output validation.

## 17.2 Required directories

Explicitly support legitimate paths such as:

```text
run_identity.json
status/
orchestration/
per_asset/
per_model/
per_shard/
model_cache/
asset_manifests/
manifests/
logs/
smoke_images/
images/
features/
sidecars/
merge_index.json
integrity_manifest.json
```

## 17.3 Security

Still reject:

* traversal;
* absolute paths;
* symlinks;
* executables;
* unexpected nested archives;
* oversized expansion;
* unsupported top-level paths;
* duplicate paths.

---

# 18. Phase M — Repair `prepare family`

Use the actual comparison registry schema.

## 18.1 Required fields

Read:

```text
prospective_or_posthoc
status
family_id
feature_spaces
metrics
sample_budgets
comparison_id
model_a
model_b
benchmark
```

## 18.2 Eligibility

A comparison is eligible only when:

```text
prospective_or_posthoc == prospective
status == registered
```

or another explicitly frozen allowed status.

## 18.3 Family completeness

Build the full hypothesis family across:

* comparisons;
* feature spaces;
* metrics;
* budgets if claim-bearing;
* kernels/bandwidths where claim-bearing.

Compute:

```text
number_of_hypotheses
alpha_total
alpha_per_hypothesis
configuration_hash
```

## 18.4 Fail closed

Reject:

* empty family;
* duplicated comparison IDs;
* missing feature caches;
* unresolved preprocessing;
* unfrozen registry;
* mixed benchmark families unless explicitly allowed;
* post hoc rows.

---

# 19. Phase N — Resume marker validation

Wire the existing validation helpers into the real orchestrator.

## 19.1 Completion marker requirements

A marker is valid only if:

```text
status == success
config_hash matches
input_hash matches
asset_hash matches
output files exist
output hashes match
schema matches
worker version matches
```

## 19.2 Invalid marker behavior

Move invalid or stale state to quarantine.

Do not silently reuse it.

## 19.3 Resume status

Emit:

```text
REUSED_VALID_COMPLETION
RERUN_INVALID_COMPLETION
RERUN_MISSING_OUTPUT
RERUN_CONFIG_CHANGED
RERUN_ASSET_CHANGED
```

---

# 20. Phase O — Final ZIP idempotence and recovery

Implement:

## 20.1 Resume

If the final ZIP exists and:

* hash matches;
* integrity manifest matches;
* all outputs match;

reuse it.

## 20.2 Rebuild

If shards are valid but ZIP is:

* missing;
* corrupt;
* hash mismatched;

rebuild only the ZIP.

## 20.3 Restart

On restart:

* quarantine old final ZIP;
* preserve raw state;
* rebuild from selected stage.

## 20.4 Force new run

Use a new run ID and output root.

## 20.5 Tests

Cover:

* valid ZIP reuse;
* corrupt ZIP rebuild;
* missing ZIP rebuild;
* changed config;
* changed asset manifest;
* partial shard;
* stale status.

---

# 21. Phase P — Portable archive completion

Repair the reproducibility archive.

## 21.1 Include

* root README;
* LICENSE;
* CITATION.cff;
* pyproject.toml;
* `.gitignore`;
* canonical notebooks;
* core code;
* tests;
* schemas;
* reports required by tests;
* final handbook;
* final hardening/closure report.

## 21.2 Exclude

* `.git`;
* raw data;
* ADE20K;
* local caches;
* Mac metadata;
* Python caches;
* quarantine;
* private outputs.

## 21.3 Git-dependent tests

Tests that require Git must:

* skip cleanly in portable mode;
* or construct a temporary fixture Git repo.

Do not fail merely because `.git` is absent.

## 21.4 Portable verification

After extracting the archive:

* run imports;
* run portable test lane;
* run notebook static checks;
* run output-schema tests;
* run synthetic runtime;
* verify required files;
* verify no forbidden metadata;
* record SHA-256;
* record member count.

---

# 22. Phase Q — End-to-end synthetic real-contract test

The synthetic pipeline must use the exact same:

* builders;
* package schemas;
* notebook worker contracts;
* importers;
* merge commands;
* cache-v2 validator;
* family builder;
* certificate engine;
* partial ranking engine.

Do not use a simplified side path.

## 22.1 Required stages

1. synthetic reference;
2. fake model preflight with smoke images;
3. fake extractor preflight;
4. generation config package;
5. two-GPU queue simulation;
6. batched fake generation;
7. generation output ZIP;
8. canonical import;
9. feature config package;
10. fake feature extraction;
11. feature output ZIP;
12. canonical import;
13. feature merge;
14. cache-v2 validation;
15. metric reproduction gate;
16. sanity gates;
17. family freeze;
18. certificate;
19. partial ranking;
20. paper firewall denial;
21. final synthetic audit.

## 22.2 Failure injection

Add tests for:

* unsupported adapter;
* missing model preflight;
* failed smoke image;
* two jobs assigned to one GPU concurrently;
* wrong local cache path;
* dependency network disabled;
* feature preflight missing;
* output schema mismatch;
* family empty due to wrong status;
* invalid resume marker;
* corrupt final ZIP;
* missing feature shard;
* duplicate feature sample ID.

---

# 23. Phase R — High-value run-readiness upgrades

Only implement upgrades that directly reduce first-run failure risk.

## 23.1 Dry package inspection command

Add:

```bash
python3 -m certgen inspect package <zip>
```

Show:

* package type;
* run ID;
* config hash;
* required assets;
* expected output;
* notebook;
* network policy;
* disk estimate;
* validation result.

## 23.2 Kaggle input validator

Add a local pre-upload command:

```bash
python3 -m certgen validate kaggle-input <zip>
```

It must emulate notebook input discovery and fail before the user uploads a bad package.

## 23.3 Post-download validator

Add:

```bash
python3 -m certgen validate kaggle-output <zip>
```

before import.

## 23.4 Run readiness command

Add:

```bash
python3 -m certgen readiness
```

Report:

```text
reference
model preflight
extractor preflight
generation package
feature package
import compatibility
cache merge
family
next action
```

## 23.5 Single exact next action

The CLI must produce one singular action based on live artifacts.

---

# 24. Phase S — Notebook regeneration

Regenerate all canonical notebooks from deterministic source.

At minimum:

```text
notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb
notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb
```

## 24.1 Preflight notebook must now include

* model preflight;
* extractor preflight;
* real model/extractor worker configs;
* one-worker-per-GPU queues;
* smoke generation;
* smoke feature extraction;
* runtime calibration;
* asset manifests;
* exact status hierarchy.

## 24.2 Generation notebook must include

* imported preflight validation;
* local snapshot loading;
* adapter-specific runtime configs;
* per-GPU queues;
* real batching;
* deterministic seed/sample mapping;
* OOM fallback;
* validated resume;
* final ZIP idempotence.

## 24.3 Feature notebook must include

* extractor preflight status validation;
* observed preprocessing contract;
* per-GPU queues;
* deterministic role shards;
* safe batch calibration;
* output schema matching the importer;
* shard-level outputs ready for local merge.

## 24.4 Static analyzer

Update checks so it validates the new real contracts.

Never label notebooks “errorless” before real Kaggle execution.

Allowed wording:

```text
run-ready by local contract
static validation passed
synthetic real-contract path passed
real Kaggle execution required
```

---

# 25. Phase T — Final local-safe verification

Run:

```text
Python compilation
package imports
default non-recursive tests
integration-audit lane
statistical lane
artifact-contract lane
runtime-closure lane
end-to-end synthetic real-contract test
model-adapter fixture tests
extractor-preflight fixture tests
per-GPU queue tests
generation parameter application tests
asset-path tests
network-policy tests
prepare preflight tests
prepare generation tests
prepare features tests
feature merge tests
prepare family tests
output-schema/import tests
resume marker tests
final ZIP recovery tests
portable archive tests
notebook static analyzer
notebook deterministic regeneration
CLI readiness tests
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

No test may:

* use the internet;
* require CUDA;
* require real CIFAR;
* load real models;
* create paper evidence.

---

# 26. Final status taxonomy

Choose exactly one:

```text
REAL_EXECUTION_CLOSURE_FAILED
REAL_EXECUTION_CLOSURE_PARTIAL_TESTS_FAILING
REAL_EXECUTION_CLOSURE_BLOCKED_BY_LOCAL_DEFECT
CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT
CVPR_REFERENCE_READY_REAL_PREFLIGHT_REQUIRED
CVPR_REAL_PREFLIGHT_READY
```

Expected likely status:

```text
CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT
```

Do not force it.

Report sub-statuses:

```text
model preflight
extractor preflight
GPU scheduling
generation adapters
asset loading
network policy
generation packaging
feature preparation
feature merge
output schema/import
family builder
resume
final ZIP
portable archive
reference
paper
```

---

# 27. Required final artifacts

Create:

```text
CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_REPORT.md
CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md

reports/CERTGEN_REAL_EXECUTION_CLOSURE_BASELINE.md
reports/CERTGEN_REAL_EXECUTION_CLOSURE_COMMAND_LEDGER.csv
reports/CERTGEN_REAL_EXECUTION_CLOSURE_CURRENT_STATE.json
reports/CERTGEN_REAL_EXECUTION_CLOSURE_REPAIR_CHANGELOG.md
reports/CERTGEN_REAL_EXECUTION_CLOSURE_TEST_MATRIX.md
reports/CERTGEN_REAL_EXECUTION_CLOSURE_NOTEBOOK_READINESS.md
reports/CERTGEN_REAL_EXECUTION_CLOSURE_ARCHIVE_AUDIT.md
reports/CERTGEN_REAL_EXECUTION_CLOSURE_HANDOFF_AUDIT.md

docs/execution/CERTGEN_REAL_MODEL_PREFLIGHT_PROTOCOL.md
docs/execution/CERTGEN_REAL_EXTRACTOR_PREFLIGHT_PROTOCOL.md
docs/execution/CERTGEN_GPU_QUEUE_SCHEDULER.md
docs/execution/CERTGEN_MODEL_ADAPTER_CONTRACT.md
docs/execution/CERTGEN_LOCAL_ASSET_LOADING_CONTRACT.md
docs/execution/CERTGEN_GENERATION_PACKAGE_CONTRACT.md
docs/execution/CERTGEN_FEATURE_PACKAGE_AND_MERGE_CONTRACT.md
docs/execution/CERTGEN_OUTPUT_SCHEMA_AND_IMPORT_CONTRACT.md
docs/execution/CERTGEN_RESUME_AND_FINAL_ZIP_RECOVERY.md
docs/execution/CERTGEN_PORTABLE_ARCHIVE_CONTRACT.md

docs/CERTGEN_CVPR_EXACT_NEXT_ACTION.md
docs/CERTGEN_CVPR_SINGLE_FILE_HANDOFF.md
```

Update existing canonical docs and clearly mark older hardening reports/handbooks as superseded.

---

# 28. Required final report structure

`CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_REPORT.md` must include:

## 1. Executive verdict

State:

* whether the real execution path is now continuous;
* whether every known handoff defect was repaired;
* whether model/extractor preflight is real;
* whether generation and feature packages are complete;
* whether canonical ZIPs import successfully;
* whether feature cache-v2 merge exists;
* whether family freeze works;
* whether resume is validated;
* whether the portable archive reproduces the portable suite;
* exact blocker;
* exact next command;
* whether any further pre-run patch is justified.

## 2. Baseline reproduction

* test counts;
* audits;
* mypy;
* paper;
* git state;
* archive state.

## 3. Defect closure matrix

For each confirmed defect:

```text
status
root cause
repair
files
tests
remaining risk
```

## 4. Real execution path

Document:

```text
reference
→ preflight package
→ model/extractor preflight
→ import
→ generation package
→ generation
→ import
→ feature package
→ extraction
→ import
→ merge
→ cache validation
→ metric gates
→ family freeze
→ certificate
→ ranking
```

## 5. Notebook readiness

For every notebook:

```text
model/extractor real preflight
GPU queueing
adapter support
asset loading
network policy
batching
resume
ZIP recovery
output schema
synthetic real-contract pass
real Kaggle run status
known risk
```

## 6. Verification

Exact commands and exit codes.

## 7. Remaining blockers

Separate:

```text
USER_REFERENCE_INPUT
REAL_KAGGLE_MODEL_PREFLIGHT
REAL_KAGGLE_EXTRACTOR_PREFLIGHT
REAL_GENERATION
REAL_FEATURE_EXTRACTION
REAL_METRIC_REPRODUCTION
REAL_CERTIFICATE
REAL_CVPR_EVIDENCE
```

## 8. Stop-building verdict

The desired conclusion, only if earned:

> No further broad or targeted pre-run infrastructure patch is justified. The repository is ready for the real CIFAR reference validation and first Kaggle preflight.

## 9. Exact next action

One command.

---

# 29. Final execution handbook requirements

The final handbook must be self-contained.

For every stage include:

```text
stage
purpose
location
CPU_or_GPU
GPU_count
network policy
input package
output package
prepare command
notebook
copy-back
validation command
import command
planning runtime
measured runtime field
disk
RAM
VRAM
resume
failure recovery
evidence class
claim permission
completion status
next action
```

The exact first critical path must be:

1. place official CIFAR-10 archive;
2. validate reference;
3. materialize reference;
4. prepare preflight package;
5. validate Kaggle input;
6. run real T4×2 preflight;
7. validate downloaded output ZIP;
8. import preflight;
9. ingest runtime calibration;
10. prepare generation package;
11. validate generation input;
12. run 1k generation;
13. validate output;
14. import generation;
15. prepare feature package;
16. validate feature input;
17. run feature extraction;
18. validate output;
19. import features;
20. merge features;
21. validate cache-v2;
22. metric reproduction;
23. sanity gates;
24. freeze family;
25. run first certificate;
26. build partial ranking;
27. stop and interpret.

---

# 30. Stop-building rule

After this pass, stop building.

Only patch further if a real execution reveals:

* model load failure;
* extractor load failure;
* Kaggle environment incompatibility;
* adapter failure;
* OOM behavior not covered;
* asset cache incompatibility;
* output import failure;
* feature merge failure;
* real metric reproduction failure;
* real evidence gate defect.

Do not build:

* new theory;
* e-BH;
* rigorous FID certification;
* video pipeline;
* dashboards;
* cloud infrastructure;
* arbitrary plugin systems;
* manuscript automation;
* more generic prompts.

---

# 31. Completion condition

This task is complete only when:

1. baseline is reproduced;
2. all defects are classified;
3. real model preflight exists;
4. real extractor preflight exists;
5. one-worker-per-GPU queueing exists;
6. model-family adapters apply frozen configs;
7. unsupported CFM stays blocked;
8. local asset loading is verified;
9. dependency and asset network policies are separated;
10. preflight package is complete;
11. generation package is complete;
12. feature package is complete;
13. feature merge into cache-v2 exists;
14. notebook and importer schemas are unified;
15. family builder uses the correct registry schema;
16. resume markers are validated;
17. final ZIP recovery is idempotent;
18. portable archive passes its declared portable suite;
19. end-to-end synthetic real-contract execution passes;
20. all local-safe tests and audits pass;
21. final status is reported;
22. one exact next command is reported;
23. the final report states whether any further pre-run patch is justified.

Begin now by inspecting the live repository and reproducing the baseline. Do not write the final verdict before verifying the implementation.
