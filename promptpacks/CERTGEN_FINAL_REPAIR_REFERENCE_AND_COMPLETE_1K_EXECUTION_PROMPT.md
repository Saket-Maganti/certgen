# CERTGEN — FINAL REPAIR, CIFAR REFERENCE INGESTION, KAGGLE T4×2 EXECUTION, AND COMPLETE 1K PILOT MASTER PROMPT

You are GPT-5.6 Codex operating as a senior research-software engineer, statistical-inference auditor, Kaggle T4×2 execution engineer, secure artifact importer, reproducibility reviewer, and evidence-integrity gatekeeper.

Repository:

```text
/Users/saketmaganti/Projects/certGen
```

This is the **single canonical state-aware master prompt** for CertGen.

It replaces separate speculative upgrade prompts and combines:

- the independent audit repair pass;
- official CIFAR-10 reference ingestion;
- all available CPU execution;
- Kaggle T4×2 diagnostic, preflight, generation, and feature handoffs;
- secure import and resume after each returned Kaggle ZIP;
- metric and sanity gates;
- confirmatory certificate execution;
- certified partial ranking;
- cross-feature analysis;
- provenance, replay, accounting, paper firewall, release verification, and final 1k pilot reporting.

Run this same prompt again after every real Kaggle output ZIP is copied back into the repository. It must discover the current state and continue automatically.

Do not ask the user which stage is active when the repository, artifact registry, and package metadata determine it.

---

# 1. Required final objective

Repair all known local defects, validate and materialize the official CIFAR-10 Python archive, execute every currently available CPU stage, prepare and validate the next Kaggle T4×2 bundle, and continue through the complete 1k pilot whenever returned Kaggle artifacts are available.

The eventual successful terminal state is:

```text
FULL_1K_CPU_ANALYSIS_COMPLETE
```

Before that, stop only at a genuine external boundary:

```text
WAITING_FOR_REFERENCE_ARCHIVE
WAITING_FOR_KAGGLE_DIAGNOSTIC
WAITING_FOR_KAGGLE_PREFLIGHT
WAITING_FOR_KAGGLE_GENERATION
WAITING_FOR_KAGGLE_FEATURES
SCIENTIFIC_GATE_FAILED
INVALID_REFERENCE_ARCHIVE
INVALID_RETURNED_KAGGLE_ARTIFACT
LOCAL_DEFECT_REMAINS
FULL_1K_CPU_ANALYSIS_COMPLETE
```

Do not create another V-numbered upgrade layer.

Do not end with generic recommendations.

Perform all available work in the current run and print one exact next action.

---

# 2. Evidence and truthfulness boundary

Until validated real execution permits otherwise:

```text
claim_allowed=false
no_empirical_claims=true
no_fake_results=true
```

Do not:

- run Kaggle or Colab from the local machine;
- initialize CUDA locally;
- fabricate generated images, features, certificates, runtimes, scores, rankings, or evidence;
- treat fixture outputs as real;
- place fixture outputs in canonical real-artifact paths;
- weaken a validator to force a pass;
- change the frozen benchmark, models, features, seeds, budgets, family membership, or thresholds because of observed outcomes;
- claim that a notebook, test, audit, or preflight image is empirical evidence;
- certify FID or polynomial KID without a separate valid proof and explicit policy;
- set `claim_allowed=true` merely because the 1k pilot completed;
- promote 1k pilot results as generalized CVPR evidence;
- start 10k, 50k, DINO, CFM, a second benchmark, or another metric family unless the prospectively frozen stop/go policy permits it.

Allowed:

- CPU-only repository repair;
- official CIFAR archive validation and materialization;
- static notebook generation and validation;
- building truthful Kaggle upload ZIPs;
- secure import of real returned Kaggle ZIPs;
- real CPU metric, certificate, ranking, and reporting work after valid feature import;
- fixture-only rehearsal under isolated fixture paths.

Every fixture artifact must contain:

```text
synthetic_validation_only
not_real_kaggle_input
not_real_kaggle_output
not_empirical_evidence
claim_allowed=false
```

---

# 3. CPU-only local policy

For compatible commands use:

```bash
export CUDA_VISIBLE_DEVICES=""
export CERTGEN_CPU_ONLY=1
```

Local tests must not:

- initialize CUDA;
- download CIFAR;
- download model checkpoints;
- require internet;
- write into real Kaggle return paths;
- mutate valid immutable real artifacts.

Unexpected local CUDA initialization or hidden internet dependency is a defect.

---

# 4. Preserve repository and user state

Before changes:

- record the current UTC time;
- record Git branch and HEAD if `.git` exists;
- record `git status --short` if Git exists;
- do not reset, clean, rebase, or discard user changes;
- do not delete real source archives, private assets, returned ZIPs, generated images, feature caches, certificates, or reports;
- do not overwrite a valid immutable artifact without an explicit content-addressed reason;
- preserve raw returned Kaggle ZIPs;
- quarantine invalid inputs instead of deleting them;
- do not create a permanent duplicate of the entire repository.

Create or update:

```text
reports/CERTGEN_MASTER_BASELINE.md
reports/CERTGEN_MASTER_CURRENT_STATE.json
reports/CERTGEN_MASTER_COMMAND_LEDGER.csv
reports/CERTGEN_MASTER_COMMAND_LEDGER.jsonl
reports/CERTGEN_MASTER_ARTIFACT_INVENTORY.csv
```

Every command record must include:

```text
sequence
phase
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

# 5. Audit the live repository, not historical reports

Inspect the actual checkout.

Do not trust completion claims solely because reports say:

```text
CERTGEN_MAX_CEILING_PRE_RUN_READY
274 passed
19/19
```

Reproduce the relevant state.

Inspect:

```text
pyproject.toml
certgen/
tests/
configs/
registry/
requirements/
scripts/
commands/
notebooks/kaggle/
artifacts/
data/
reports/
docs/
paper/
release/
dist/
```

Identify:

- actual CLI entry points;
- actual artifact registry;
- current reference status;
- current Kaggle input and incoming-output paths;
- current family definition;
- current certificate assumptions;
- current sanity-gate implementations;
- current dependency locks;
- current notebooks;
- current release-building logic;
- current paper evidence firewall.

---

# 6. Discover and use the real CLI

Run help before invoking commands:

```bash
python3 -m certgen --help
python3 -m certgen readiness --help
python3 -m certgen next-action --help
python3 -m certgen doctor --help
python3 -m certgen validate --help
python3 -m certgen kaggle --help
python3 -m certgen notebooks --help
python3 -m certgen audit --help
```

Use actual signatures.

Do not invent flags, commands, or paths.

If a required command surface is missing, implement it narrowly over existing builders and registries rather than creating a parallel framework.

---

# 7. Mandatory independent-audit repairs

Complete every repair in this section before claim-bearing execution.

## 7.1 Separate controls from the confirmatory certificate family

The current design included:

- null reference split;
- obvious-gap corruption control;
- checkpoint/model comparison;

under both Inception and CLIP, producing a six-hypothesis family.

The control constructions may involve:

- finite-population sampling without replacement;
- paired clean/corrupted samples sharing the same source image;
- dependence structures not covered by the existing IID-with-replacement union-Hoeffding theorem;
- incomplete source-lineage preservation in certificate bundles.

Unless the repository already contains a complete, reviewed theorem and implementation covering these exact sampling processes, make the safe contract:

```text
null controls = mandatory sanity gates
obvious-gap controls = mandatory sanity gates
controls_claim_allowed = false
controls_in_confirmatory_family = false
```

The claim-bearing minimum family must contain exactly:

```text
checkpoint/model comparison under Inception
checkpoint/model comparison under CLIP
```

Expected family size:

```text
2
```

Preserve control results as real scientific diagnostics, but label them:

```text
sanity_control_only
not_confirmatory_certificate
claim_allowed=false
```

Update:

- study/profile configuration;
- family builder;
- multiplicity allocation;
- certificate-input builder;
- operational-family completeness checks;
- ranking requirements;
- cross-feature analysis;
- paper result contracts;
- claim-evidence matrix;
- fixture rehearsals;
- documentation;
- tests.

If a theorem covering the control streams already genuinely exists, verify all assumptions and source-lineage contracts. Do not assume validity from naming alone.

## 7.2 Preserve complete source lineage

For null and corruption controls, preserve:

```text
sample_id
source_id
source_role
clean_or_corrupted
corruption_type
corruption_severity
corruption_seed
reference_draw_id
study_hash
preprocessing_hash
```

Do not rely only on A/B sample IDs when both derive from the same underlying source.

Validate:

- no unintended overlap;
- intended pairing is explicit;
- source identities are recoverable;
- manifests and downstream gates agree;
- provenance records include parent source artifacts.

## 7.3 Replace placeholder or duplicated sanity checks

Inspect the current sanity implementation, especially `certgen/cvpr/post_cache.py` and related modules.

Do not accept hard-coded values such as:

```text
repeated_batching = 0.0
repeated_shard_merge = 0.0
```

Implement real checks.

### Repeated batching

Run the same extractor and role set through at least two valid batch sizes using identical ordered inputs.

Compare:

- sample IDs;
- feature shapes;
- dtypes;
- finite values;
- maximum absolute feature difference;
- resulting metric difference.

Use prospectively documented tolerances.

### Repeated shard merge

Independently construct equivalent feature outputs using at least:

```text
one-shard path
two-shard path
```

or another deterministic alternative supported by the repository.

Compare:

- ordered sample IDs;
- row coverage;
- hashes where exact equality is expected;
- numerical tolerances where floating-point variation is allowed;
- resulting metrics.

Do not merely reread the same merged file.

### Corruption ladder

Create a deterministic prospective control ladder with multiple severities.

At minimum, use one primary corruption family with at least three nonzero severities plus the clean baseline.

Prefer a simple, reproducible corruption such as:

```text
Gaussian blur
```

Additional noise and JPEG lanes may be sensitivity-only.

Freeze:

- corruption function;
- library/version;
- parameters;
- seed;
- severity values;
- expected directional rule;
- pass/fail criteria.

Do not reuse one fixed-blur result under several different names.

Do not require strict monotonicity unless justified prospectively. At minimum require:

- the severe corruption is measurably farther from reference than clean;
- direction is correct;
- gaps exceed the frozen tolerance;
- no preprocessing mismatch exists.

### Actual nonclaim control certificates

Where the project reports “certificate-controlled ordering,” run the real certificate implementation over the control streams using an explicitly nonclaim configuration.

Label outputs:

```text
control_validation_only
not_in_confirmatory_family
claim_allowed=false
```

This validates code behavior without silently asserting theorem-backed confirmatory status.

## 7.4 Align dependency profiles and lock files

Inspect actual imports in:

- diagnostic notebook and workers;
- preflight notebook and workers;
- generation notebook and workers;
- feature notebook and workers;
- CLIP loader;
- Inception loader.

The audit found a possible mismatch involving:

```text
timm
open-clip-torch
```

while the active CLIP route appeared Transformers-based.

Choose one actual minimal route.

Preferred rule:

- if the active pilot uses Transformers CLIP and does not import `timm` or `open_clip`, remove them from the required compatibility profile;
- if they are actually required, add exact compatible versions to the relevant lock files and test the imports.

Create or validate:

```text
requirements/kaggle-base.lock
requirements/kaggle-preflight.lock
requirements/kaggle-generation.lock
requirements/kaggle-features.lock
requirements/kaggle-constraints.txt
```

Requirements must cover all real notebook and worker imports.

Every notebook must generate:

```text
dependency_report.json
dependency_freeze.txt
pip_check.txt
```

No local dependency test may download packages.

## 7.5 Fix the monolithic pytest order/stall defect

The independent audit found that selected test groups passed in isolation, while the one-process full suite stalled around an environment-bootstrap runtime test.

Reproduce the issue with:

- one clean process;
- one canonical full-suite command;
- deterministic timeout diagnostics;
- verbose last-test reporting;
- `faulthandler`;
- subprocess and multiprocessing cleanup inspection.

Identify the actual cause, such as:

- leaked environment variables;
- leaked monkeypatch/global state;
- import metadata cache;
- unclosed subprocess;
- unjoined multiprocessing worker;
- changed current directory;
- temporary-path state;
- signal handler;
- file lock;
- module singleton.

Fix the root cause.

Do not merely split the official test command into batches to hide it.

Acceptance requirement:

```text
the canonical full local-safe pytest suite completes in one process
```

Focused batches may still be retained for diagnosis.

## 7.6 Repair release packaging

Ensure user-facing source and release ZIPs include required root files:

```text
.gitignore
pyproject.toml
README.md
release/archive_manifest.json
```

Exclude:

```text
__MACOSX/
.DS_Store
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
temporary logs
fixture outputs in real paths
restricted/private weights
credentials
```

Rebuild the canonical release archive deterministically.

Perform a fresh-extraction audit in a clean temporary directory:

- safe extraction;
- compileall;
- imports;
- canonical local-safe tests;
- portable tests;
- notebook static validation;
- paper firewall;
- privacy scan;
- restricted-asset scan;
- archive manifest verification.

Record:

```text
archive path
member count
size
SHA-256
fresh-extraction verification
```

## 7.7 Add a canonical private asset preparation workflow

CIFAR is the first blocker, but preflight also needs model and extractor assets.

Create or validate one canonical workflow covering:

```text
google DDPM CIFAR-10 checkpoint
Frank DDPM EMA CIFAR-10 checkpoint
Inception weights
CLIP weights
```

The workflow must support the repository’s selected mode:

```text
KAGGLE_INTERNET_ON_INSTALL
PRIVATE_KAGGLE_DATASET
USER_PROVIDED_VALIDATED_CACHE
USE_PREINSTALLED_VALIDATED
```

Create or update:

```text
KAGGLE_ASSET_SETUP.md
registry/assets/
scripts/prepare_kaggle_private_assets.py
commands/kaggle/prepare_private_assets.sh
```

Each asset record must include:

```text
asset_id
provider
repository_or_mount
revision
expected_files
expected_hashes
loader
license_status
redistribution_allowed
public_archive_included
private_mount_required
internet_required
```

Do not include restricted CLIP or checkpoint weights in public archives unless redistribution is explicitly verified.

Absent assets must fail early with an exact remedy.

---

# 8. Reproduce the repaired local baseline

After repairs, run each unique local-safe lane exactly as needed:

- `compileall`;
- import checks;
- canonical one-process full pytest suite;
- explicit integration audits once;
- statistical tests;
- artifact-contract tests;
- runtime-hardening tests;
- post-cache tests;
- final-readiness tests;
- maximum-ceiling tests;
- Kaggle-bundle tests;
- notebook tests;
- provenance tests;
- replay tests;
- paper-firewall tests;
- claim-evidence tests;
- release tests;
- Ruff;
- critical changed-code mypy;
- full mypy debt comparison;
- notebook deterministic-regeneration check;
- privacy scan;
- secrets scan;
- restricted-asset scan;
- release scan;
- documented paper compilation;
- final pre-run audit;
- maximum-ceiling audit;
- CPU-execution audit;
- Kaggle-launch audit;
- `git diff --check` when Git exists.

Do not recursively execute the same full suite several times.

Historical full-project mypy debt may remain only if:

- it is clearly documented;
- changed-code mypy is clean;
- the error count does not increase.

---

# 9. Locate and validate the official CIFAR-10 Python archive

Canonical expected path:

```text
/Users/saketmaganti/Projects/certGen/data/sources/cifar-10-python.tar.gz
```

The user will provide this archive.

Search only reasonable local locations:

```text
repository data/sources/
repository root
current working directory
/Users/saketmaganti/Downloads
```

Use exact filename and package structure, not loose semantic matching.

If exactly one valid candidate is found outside the canonical location:

1. compute size and hashes;
2. inspect safely without extraction;
3. verify it matches the official CIFAR-10 Python archive contract expected by the repository;
4. copy it atomically to the canonical source path;
5. preserve the original;
6. register provenance.

If multiple candidates are present, inspect and select only when one validates unambiguously. Otherwise stop with a candidate report.

Do not rename the previously downloaded Kaggle `train.7z` as the Python archive.

Do not use:

```text
train.7z
test.7z
sampleSubmission.csv
```

when the official Python archive is available.

Validate using the actual CertGen CLI.

Expected conceptual checks:

- archive type;
- safe member paths;
- expected CIFAR batch structure;
- expected counts;
- label validity;
- image dimensions;
- decoded content;
- no duplicate IDs;
- source hash;
- license/provenance record.

If missing:

```text
WAITING_FOR_REFERENCE_ARCHIVE
```

Print the exact expected path.

If invalid:

```text
INVALID_REFERENCE_ARCHIVE
```

Do not continue to real study materialization.

---

# 10. Materialize and register the CIFAR reference

After validation:

- materialize the canonical reference representation;
- preserve source archive hash;
- create deterministic sample IDs;
- create source IDs;
- create class labels where needed for validation;
- verify exactly the expected population;
- verify decoding;
- verify image mode and dimensions;
- verify no duplicate or missing IDs;
- create and register the reference manifest;
- validate lineage;
- validate content hashes;
- preserve immutable source-to-materialized mapping.

Do not use the Kaggle competition test set for the initial pilot.

---

# 11. Freeze the prospective 1k study

After reference materialization:

- select the canonical minimal CIFAR integrity profile;
- freeze the study;
- freeze selected model roster;
- freeze Inception and CLIP feature definitions;
- freeze preprocessing;
- freeze support/bounded-kernel settings;
- freeze RBF bandwidth rule;
- freeze 1k budget;
- freeze generation seeds;
- freeze reference draw;
- freeze control allocations;
- freeze confirmatory family size 2;
- freeze multiplicity allocation;
- freeze sanity thresholds;
- freeze stop/go rules;
- freeze runtime planning;
- freeze prospective sensitivity lanes.

Do not activate 10k, 50k, CFM, DINO, a second benchmark, or a third feature space.

Validate:

- reference-role non-overlap;
- intended control source relationships;
- complete source lineage;
- study hashes;
- provenance;
- deterministic replay;
- paper firewall.

---

# 12. Canonical Kaggle T4×2 notebooks

Ensure these exist and are the active canonical notebooks:

```text
notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb
```

Every notebook must:

- instruct the user to select `GPU T4 ×2`;
- verify exactly two visible CUDA devices for the dual-GPU path;
- use multiprocessing `spawn`;
- avoid parent CUDA initialization before spawn;
- use one active worker per physical GPU;
- deterministically partition ordered seeds or rows;
- preserve study/profile/configuration hashes;
- validate dependencies before model/extractor loading;
- validate assets before expensive work;
- run a tiny non-evidentiary dual-GPU check;
- measure model load, warmup, throughput, peak VRAM, and safe batch size;
- support deterministic resume;
- write shards atomically;
- use explicit worker-contract versions;
- produce status files;
- produce member hashes;
- create and revalidate one output ZIP;
- support multipart fallback when required;
- print one exact local copy-back path;
- print one exact local resume command;
- convert common failures into actionable blocked statuses.

Required notebook sections:

```text
0 Human instructions
1 Immutable user configuration
2 Input discovery
3 Environment diagnostics
4 Dependency setup and validation
5 Asset discovery and validation
6 Configuration/provenance validation
7 Tiny dual-GPU non-evidence check
8 Runtime calibration
9 Full parallel execution
10 Merge and validation
11 Atomic output ZIP
12 Local handoff
```

Do not store executed outputs in committed notebooks.

---

# 13. Kaggle bundle command surface

Ensure the live CLI supports the actual equivalent of:

```bash
python3 -m certgen kaggle inventory
python3 -m certgen kaggle build-input --stage diagnostic
python3 -m certgen kaggle build-input --stage preflight --profile cifar_integrity_minimal
python3 -m certgen kaggle build-input --stage generation --scale 1k --study <study>
python3 -m certgen kaggle build-input --stage features --scale 1k --study <study>
python3 -m certgen kaggle validate-input <zip>
python3 -m certgen kaggle inspect-input <zip>
python3 -m certgen kaggle next --explain
```

Use the actual CLI signatures.

Build only truthful inputs whose real parents exist.

Canonical directories:

```text
artifacts/cvpr/kaggle_inputs/diagnostic/
artifacts/cvpr/kaggle_inputs/preflight/
artifacts/cvpr/kaggle_inputs/generation/
artifacts/cvpr/kaggle_inputs/features/
artifacts/cvpr/kaggle_inputs/fixture_only/
```

Static bundles that may exist before real GPU execution:

```text
certgen_kaggle_environment_diagnostic_input.zip
certgen_cvpr_preflight_input.zip
```

Generation input must require valid imported preflight output.

Feature input must require valid imported generation output and real CPU-built controls.

Do not create fake real generation or feature input ZIPs.

---

# 14. State-aware CPU autorun

Create or harden:

```text
scripts/run_all_available_cpu_stages.py
commands/cpu/run_all_available_cpu_stages.sh
```

The orchestrator must:

- run CPU-only;
- query actual readiness;
- discover registered real artifacts;
- discover returned Kaggle ZIPs by package metadata;
- validate them securely;
- import them only after validation;
- execute every available CPU stage;
- build the next real Kaggle upload ZIP;
- stop only at a genuine external boundary;
- continue automatically through final analysis after feature import;
- be idempotent;
- be resumable;
- never promote fixtures;
- log all actions;
- return stable exit codes.

Required invocation:

```bash
python3 scripts/run_all_available_cpu_stages.py \
  --resume \
  --explain
```

Suggested exit codes:

```text
0  CPU_AVAILABLE_STAGES_COMPLETE
10 WAITING_FOR_REFERENCE_ARCHIVE
11 WAITING_FOR_KAGGLE_DIAGNOSTIC
12 WAITING_FOR_KAGGLE_PREFLIGHT
13 WAITING_FOR_KAGGLE_GENERATION
14 WAITING_FOR_KAGGLE_FEATURES
20 SCIENTIFIC_GATE_FAILED
30 LOCAL_DEFECT
40 INVALID_REFERENCE_ARCHIVE
41 INVALID_RETURNED_KAGGLE_ARTIFACT
```

Readiness views must agree:

```bash
python3 -m certgen readiness --explain --json
python3 -m certgen next-action --explain
python3 -m certgen doctor --json
python3 -m certgen kaggle next --explain
```

A disagreement is a local defect.

---

# 15. Secure discovery and import of returned Kaggle ZIPs

Inspect canonical incoming paths and artifact registry.

Classify each candidate by package metadata:

```text
DIAGNOSTIC_OUTPUT
PREFLIGHT_OUTPUT
GENERATION_OUTPUT
FEATURE_OUTPUT
NONE
AMBIGUOUS
INVALID
```

Do not classify by filename alone.

Before extraction:

- reject traversal;
- reject absolute paths;
- reject symlinks;
- validate package type;
- validate run identity;
- validate study/profile/configuration hashes;
- validate worker contract;
- validate dependency report;
- validate asset report;
- validate completion markers;
- validate member hashes;
- validate exact seed or row coverage;
- reject stale outputs;
- reject duplicates;
- reject partial packages unless the contract explicitly supports resumable multipart import;
- reject fixture markers;
- quarantine invalid packages.

Preserve the raw ZIP after valid import.

---

# 16. Kaggle diagnostic stage

When no valid diagnostic return exists:

- build and validate the diagnostic input ZIP;
- validate the diagnostic notebook;
- update the launchboard;
- stop with:

```text
WAITING_FOR_KAGGLE_DIAGNOSTIC
```

Report:

```text
input ZIP
input ZIP SHA-256
notebook
accelerator GPU T4 ×2
internet setting
expected output ZIP
local copy-back path
exact resume command
```

When a valid diagnostic return exists:

- import it;
- register GPU and environment information;
- verify two T4 GPUs;
- verify multiprocessing behavior;
- verify disk/write checks;
- verify dependency mode;
- preserve measured runtime records separately from planning estimates;
- update preflight operational settings when justified;
- continue automatically to preflight preparation.

---

# 17. Kaggle model/extractor preflight stage

When no valid preflight return exists:

- build and validate the preflight input ZIP;
- verify private asset instructions;
- verify notebook deterministic generation;
- stop with:

```text
WAITING_FOR_KAGGLE_PREFLIGHT
```

When a valid preflight return exists:

- import it;
- verify both selected generative checkpoints;
- verify Inception;
- verify CLIP;
- verify revisions and hashes;
- ingest model/extractor load time;
- ingest warmup and throughput;
- ingest safe batch sizes;
- ingest peak VRAM;
- preserve planning estimates as planning estimates;
- fail closed on any required model/extractor failure;
- build and validate the real 1k generation input ZIP;
- create its run capsule;
- register its provenance;
- update replay;
- continue to the generation boundary.

---

# 18. Kaggle 1k generation stage

Canonical pilot:

```text
two selected CIFAR-10 checkpoint candidates
1,000 images per model
GPU 0 and GPU 1 deterministic seed partition
```

When no valid generation return exists:

- verify the generation input ZIP;
- verify exact seed plan;
- verify worker contract;
- verify notebook;
- stop with:

```text
WAITING_FOR_KAGGLE_GENERATION
```

When a valid generation return exists:

- import it;
- verify exact model coverage;
- verify exactly 1,000 expected samples per selected model;
- verify complete seed coverage;
- reject duplicate or missing seeds;
- decode every image or use a complete validated decode pass;
- verify dimensions and RGB mode;
- verify image hashes;
- verify checkpoint identity;
- verify per-shard and merged manifests;
- register generated-image artifacts;
- update provenance and replay.

Then build real controls.

---

# 19. Real CPU control construction

Build:

```text
deterministic null reference control
deterministic obvious-gap corruption control
```

Controls are mandatory sanity gates, not confirmatory family members.

Validate:

- source IDs;
- reference draw IDs;
- no unintended overlap;
- intended clean/corrupt pairing;
- corruption parameters;
- corruption seeds;
- exact counts;
- image hashes;
- manifests;
- provenance.

Build the prospectively frozen corruption ladder and actual nonclaim control-certificate inputs.

Label all control-certificate outputs:

```text
sanity_control_only
not_confirmatory_certificate
claim_allowed=false
```

After controls pass structural validation, build the real feature-extraction input ZIP.

---

# 20. Kaggle feature extraction stage

Required roles include the real roles needed for:

- reference;
- each selected generated model;
- null controls;
- corruption controls.

Required extractors:

```text
Inception
CLIP
```

When no valid feature return exists:

- validate the real feature input ZIP;
- verify ordered manifests;
- verify role counts;
- verify preprocessing locks;
- verify private assets;
- verify deterministic row partition;
- stop with:

```text
WAITING_FOR_KAGGLE_FEATURES
```

When a valid feature return exists:

- import it;
- validate both extractors;
- validate every required role;
- verify exact row coverage;
- reject duplicate and missing rows;
- verify ordered sample IDs;
- verify source IDs for controls;
- verify shapes;
- verify dtypes;
- verify finite values;
- verify preprocessing hashes;
- verify extractor revisions;
- verify shard manifests;
- verify deterministic merge;
- register feature artifacts;
- merge into canonical cache-v2;
- validate all caches;
- register merged caches;
- update provenance and replay.

Do not stop after feature import.

---

# 21. Run real metric and sanity gates

After valid cache-v2 artifacts exist:

- freeze metric-reproduction configuration;
- freeze sanity configuration;
- run point-estimate reproduction where applicable;
- run feature alignment checks;
- run null-control checks;
- run corruption-direction checks;
- run the multi-severity corruption ladder;
- run actual repeated-batching checks;
- run actual independent shard-merge checks;
- run actual nonclaim control certificates;
- verify preprocessing and representation contracts;
- verify bounded-kernel assumptions;
- verify support normalization;
- verify no NaNs or infinities;
- verify no hidden role leakage.

Do not weaken thresholds after seeing outputs.

If a required gate fails:

```text
SCIENTIFIC_GATE_FAILED
```

Preserve:

- diagnostics;
- failing artifacts;
- exact reason;
- rerun frontier;
- whether the problem is data, feature extraction, preprocessing, metric, or theory.

Do not proceed to confirmatory certificates.

---

# 22. Build the two-hypothesis confirmatory family

After all mandatory gates pass:

Freeze exactly:

```text
checkpoint/model comparison under Inception
checkpoint/model comparison under CLIP
```

Validate:

- family size = 2;
- unique hypothesis IDs;
- alpha allocation;
- sample budgets;
- feature definitions;
- reference roles;
- model roles;
- bounded-kernel settings;
- reference-draw identity;
- no control hypotheses in the confirmatory family;
- no missing or extra bundles.

Build every certificate-input bundle using canonical builders.

Validate:

```text
features_a
features_b
features_r
sample_ids_a
sample_ids_b
source_ids_r
study_hash
feature_hash
preprocessing_hash
family_hash
```

Use actual required schema from the repository.

---

# 23. Execute all confirmatory CPU certificates

Run every missing certificate.

Do not stop after the first.

Reuse a completed certificate only when:

- all parent hashes match;
- code/configuration hashes match;
- family hash matches;
- artifact validation passes.

Verify:

- time-uniform method;
- bounded-stream assumptions;
- alpha allocation;
- first-crossing decision;
- direction;
- sample count at first decision;
- censoring when unresolved;
- maximum budget;
- lineage;
- no duplicate result;
- complete family coverage.

Produce certificate lineage cards.

The 1k results remain:

```text
pilot_only
single_benchmark_only
not_generalized
```

Do not automatically set broad `claim_allowed=true`.

---

# 24. Build the certified partial ranking

Require complete confirmatory certificate coverage or prospectively frozen exclusions.

Do not force a total order.

Produce:

```text
ranking_graph.json
ranking_edges.csv
ranking_unresolved.csv
ranking_invalid.csv
ranking_provenance.json
```

Every edge must link to supporting certificate IDs and parent hashes.

With only two model candidates, the result may be:

- one certified direction;
- unresolved;
- invalid due to failed assumptions.

Report it honestly.

---

# 25. Cross-feature analysis

Produce:

```text
agreement_matrix.csv
direction_disagreements.csv
decided_vs_unresolved.csv
invalid_feature_lanes.csv
consensus_edges.json
representation_specific_edges.json
```

Apply the frozen policy.

Do not call Inception/CLIP disagreement an implementation failure unless their contracts unexpectedly differ or validation fails.

Distinguish:

```text
agreement
representation-specific decision
unresolved in one or both spaces
invalid lane
```

---

# 26. Accounting, provenance, replay, and claim-evidence closure

Complete:

- measured CPU durations;
- measured Kaggle durations from returned logs;
- model load time;
- generation GPU seconds;
- feature GPU seconds;
- CPU merge time;
- certificate CPU time;
- first-decision sample count;
- fixed-budget sample count;
- retrospective sample savings;
- disk sizes;
- ZIP sizes;
- provenance DAG;
- provenance verification;
- deterministic replay plan;
- minimum rerun frontier;
- artifact inventory;
- claim-evidence matrix;
- paper firewall;
- figure/table data-contract validation;
- pilot stop/go report.

Use labels:

```text
PLANNING_ESTIMATE_NOT_MEASURED
MEASURED_KAGGLE_PREFLIGHT
MEASURED_REAL_RUN
DERIVED_FROM_MEASURED_RUN
```

Never present a planning estimate as measured.

---

# 27. Paper and evidence policy

The paper may receive only validated placeholders and real pilot artifacts after gates pass.

Do not:

- insert fixture values;
- imply multi-benchmark generality;
- imply leaderboard-wide validation;
- claim CVPR readiness from one 1k pilot;
- certify FID;
- describe controls as confirmatory certified comparisons;
- hide unresolved or invalid outcomes.

The paper must state the exact scope:

```text
CIFAR-10
two checkpoint candidates
Inception and CLIP
1k pilot
two-hypothesis confirmatory family
controls used as sanity diagnostics
```

Keep `claim_allowed=false` unless the repository’s explicit evidence policy permits a narrowly scoped pilot claim. Even then, do not unlock generalized claims.

---

# 28. Complete builder-faithful fixture rehearsal

In isolated fixture paths, run the actual builder chain:

```text
diagnostic input
→ fake diagnostic return
→ secure import
→ preflight input
→ fake preflight return
→ secure import
→ generation input
→ fake dual-GPU generation return
→ secure import
→ controls
→ feature input
→ fake dual-GPU feature return
→ secure import
→ cache-v2
→ real sanity-code paths
→ two-hypothesis family
→ all fixture certificates
→ partial ranking
→ cross-feature outputs
```

No manually fabricated shortcut certificate inputs.

Negative tests must cover:

- zero GPU;
- one GPU;
- ambiguous ZIP;
- dependency conflict;
- missing asset;
- stale worker contract;
- duplicate seed;
- missing seed;
- duplicate feature row;
- missing feature row;
- wrong extractor revision;
- changed preprocessing;
- changed study hash;
- partial ZIP;
- ZIP traversal;
- symlink member;
- corrupt multipart package;
- fixture in real path;
- incomplete confirmatory family;
- premature ranking;
- unauthorized `claim_allowed=true`;
- control hypothesis accidentally reintroduced into the confirmatory family.

---

# 29. Required final verification

At each intermediate boundary, run focused affected checks.

Before finalizing a repair/execution pass, run:

- compileall;
- imports;
- canonical one-process full local-safe pytest;
- explicit integration audits;
- Ruff;
- critical changed-code mypy;
- full mypy debt comparison;
- notebook deterministic-regeneration validation;
- notebook static analyzer;
- Kaggle input validation;
- provenance verification;
- replay verification;
- paper firewall;
- privacy scan;
- secrets scan;
- restricted-asset scan;
- release scan;
- paper compilation;
- final pre-run audit;
- maximum-ceiling audit;
- CPU-execution audit;
- Kaggle-launch audit;
- `git diff --check` when applicable.

Require readiness views to agree.

---

# 30. Required reports and artifacts

Create or update:

```text
CERTGEN_FINAL_REPAIR_AND_EXECUTION_REPORT.md
CERTGEN_CURRENT_NEXT_ACTION.md
CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md
CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md
CERTGEN_KAGGLE_INPUT_BUNDLE_CATALOG.md
CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md
CERTGEN_1K_PILOT_FINAL_EXECUTION_REPORT.md
CERTGEN_1K_PILOT_STOP_GO_REPORT.md

reports/CERTGEN_MASTER_BASELINE.md
reports/CERTGEN_MASTER_CURRENT_STATE.json
reports/CERTGEN_MASTER_COMMAND_LEDGER.csv
reports/CERTGEN_MASTER_COMMAND_LEDGER.jsonl
reports/CERTGEN_MASTER_ARTIFACT_INVENTORY.csv
reports/CERTGEN_AUDIT_REPAIR_REPORT.md
reports/CERTGEN_REFERENCE_VALIDATION_REPORT.md
reports/CERTGEN_SANITY_GATE_REPORT.md
reports/CERTGEN_CONFIRMATORY_FAMILY_REPORT.md
reports/CERTGEN_CERTIFICATE_COVERAGE_REPORT.md
reports/CERTGEN_CROSS_FEATURE_REPORT.md
reports/CERTGEN_PROVENANCE_VERIFICATION.md
reports/CERTGEN_REPLAY_REPORT.md
reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv
reports/CERTGEN_RELEASE_VERIFICATION.md
reports/CERTGEN_FINAL_AUDIT.md
```

At every Kaggle boundary, the next-action report must contain:

```text
completed stage
next notebook
input ZIP
input ZIP SHA-256
accelerator
internet mode
private assets
expected output ZIP
local copy-back path
exact resume command
```

---

# 31. Final response requirements

Report:

1. What repository state was found?
2. Which audit defects were reproduced?
3. Which defects were fixed?
4. Does the full one-process test suite pass?
5. Does the release fresh-extraction audit pass?
6. Was the official CIFAR archive found?
7. Was it valid?
8. Was it materialized?
9. Was the study frozen?
10. Is the confirmatory family exactly two hypotheses?
11. Are controls sanity-only?
12. Which Kaggle inputs exist?
13. Which returned Kaggle ZIP was found, if any?
14. Was it valid and imported?
15. Which CPU stages ran?
16. Which next Kaggle ZIP was built?
17. Which notebook is next?
18. What accelerator and internet/private-asset mode are required?
19. Where must the next output ZIP be placed?
20. What exact resume command must be run?
21. If features exist, did all mandatory gates pass?
22. Were all confirmatory certificates completed?
23. Was the partial ranking built?
24. Was cross-feature analysis completed?
25. Are claims still blocked or narrowly unlocked?
26. Does any local defect remain?
27. What is the exact final status?

Choose exactly one final status:

```text
WAITING_FOR_REFERENCE_ARCHIVE
WAITING_FOR_KAGGLE_DIAGNOSTIC
WAITING_FOR_KAGGLE_PREFLIGHT
WAITING_FOR_KAGGLE_GENERATION
WAITING_FOR_KAGGLE_FEATURES
SCIENTIFIC_GATE_FAILED
INVALID_REFERENCE_ARCHIVE
INVALID_RETURNED_KAGGLE_ARTIFACT
LOCAL_DEFECT_REMAINS
FULL_1K_CPU_ANALYSIS_COMPLETE
```

At a Kaggle boundary, do not recommend another build prompt.

Print the one exact next Kaggle action.

After `FULL_1K_CPU_ANALYSIS_COMPLETE`, do not automatically expand the study. Report the frozen stop/go decision and wait for explicit authorization.

Begin now by preserving repository state, discovering the actual CLI, reproducing the audit defects, fixing them, locating the official CIFAR-10 Python archive, and executing every currently available CPU stage.
