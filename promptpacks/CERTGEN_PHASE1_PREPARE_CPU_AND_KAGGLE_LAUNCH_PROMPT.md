# CERTGEN — PHASE 1: COMPLETE ALL PRE-GPU CPU WORK, BUILD KAGGLE INPUTS, AND HARDEN T4×2 RUNBOOKS

You are GPT‑5.6 Codex operating as a senior research-software engineer, Kaggle T4×2 execution engineer, scientific-computing auditor, and CVPR reproducibility reviewer.

Repository:

```text
/Users/saketmaganti/Projects/certGen
```

Your task is to complete **all work that must happen before the first real Kaggle GPU run**.

This replaces the previous separate Kaggle-packaging and initial CPU-execution prompts.

Do not stop after generating notebooks.

Do not stop after running tests.

Continue automatically through every available local CPU stage until the next required action is a real Kaggle T4×2 run or the official CIFAR archive is genuinely missing.

Choose exactly one final status:

```text
PHASE1_COMPLETE_WAITING_FOR_REFERENCE
PHASE1_COMPLETE_WAITING_FOR_KAGGLE_DIAGNOSTIC
PHASE1_COMPLETE_WAITING_FOR_KAGGLE_PREFLIGHT
PHASE1_LOCAL_DEFECT_REMAINS
```

Desired status when CIFAR is present and all preparation succeeds:

```text
PHASE1_COMPLETE_WAITING_FOR_KAGGLE_DIAGNOSTIC
```

or, if the diagnostic is optional/already satisfied:

```text
PHASE1_COMPLETE_WAITING_FOR_KAGGLE_PREFLIGHT
```

---

# 1. Truthfulness boundary

Do not:

- run Kaggle or Colab;
- initialize CUDA locally;
- download CIFAR;
- download large model checkpoints during local tests;
- fabricate generated images, feature arrays, GPU results, or runtimes;
- place fixture packages in real upload paths;
- set `claim_allowed=true`;
- populate empirical paper results;
- claim real T4×2 success without a returned Kaggle artifact.

Allowed:

- CPU-only execution;
- validation of a locally present official CIFAR archive;
- CIFAR materialization;
- profile, study, scale, sensitivity, and reference-draw freezing;
- dependency and asset contract creation;
- notebook generation and static validation;
- building static diagnostic and preflight upload ZIPs;
- isolated fixture-only rehearsals.

All fixture artifacts must contain:

```text
synthetic_validation_only
not_real_kaggle_input
not_empirical_evidence
claim_allowed=false
```

---

# 2. CPU-only policy

For compatible local commands use:

```text
CUDA_VISIBLE_DEVICES=""
CERTGEN_CPU_ONLY=1
```

Any unexpected CUDA initialization is a local defect.

Do not use internet access for local tests.

---

# 3. Preserve repository state

Before changes:

- record Git branch and HEAD;
- record `git status --short`;
- preserve user changes;
- do not reset or clean the repository;
- do not delete real inputs or returned outputs;
- do not overwrite valid immutable artifacts;
- do not create a permanent backup;
- do not restore ADE20K.

Create:

```text
reports/CERTGEN_PHASE1_BASELINE.md
reports/CERTGEN_PHASE1_COMMAND_LEDGER.csv
reports/CERTGEN_PHASE1_CURRENT_STATE.json
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

# 4. Discover the real CLI

Inspect actual help before executing:

```bash
python3 -m certgen --help
python3 -m certgen readiness --help
python3 -m certgen next-action --help
python3 -m certgen doctor --help
python3 -m certgen kaggle --help
python3 -m certgen notebooks --help
python3 -m certgen audit --help
```

Use live CLI signatures.

Do not invent unsupported flags or paths.

---

# 5. Reproduce the local baseline

Run all unique local-safe lanes:

- compileall;
- imports;
- default non-recursive pytest;
- explicit integration audit once;
- statistical tests;
- artifact-contract tests;
- runtime-hardening tests;
- real-execution closure tests;
- final-readiness tests;
- post-cache repair tests;
- maximum-ceiling tests;
- Kaggle-bundle tests;
- notebook tests;
- provenance tests;
- replay tests;
- claim-evidence tests;
- release tests;
- Ruff;
- critical changed-code mypy;
- full mypy debt comparison;
- notebook deterministic-regeneration check;
- paper firewall;
- privacy scan;
- restricted-asset scan;
- release scan;
- documented paper compilation;
- final pre-run audit;
- maximum-ceiling audit;
- Kaggle-launch audit when present;
- `git diff --check`.

Do not recursively run the same full suite several times.

Historical full-mypy debt may remain only if it does not increase.

---

# 6. Complete the Kaggle bundle command surface

Ensure these canonical commands exist and work:

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

Support `--json`, `--explain`, and `--dry-run` where appropriate.

If missing, implement them narrowly using existing builders rather than adding a parallel architecture.

---

# 7. Canonical T4×2 notebooks

Ensure these exist:

```text
notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb
```

Every notebook must:

- instruct the user to select `GPU T4 ×2`;
- verify two visible CUDA devices;
- use multiprocessing `spawn`;
- avoid parent CUDA initialization before spawn;
- use one active worker per physical GPU;
- deterministically partition ordered seeds or rows;
- preserve study/profile/configuration hashes;
- validate dependencies before loading models;
- validate assets before expensive work;
- run a tiny non-evidentiary test on both GPUs;
- measure model load, warmup, throughput, VRAM, and safe batch size;
- support hash-safe resume;
- write shards atomically;
- create and revalidate one output ZIP;
- support multipart fallback;
- print one exact local import/resume command;
- convert common failures into actionable status files.

Required notebook structure:

```text
0 Human instructions
1 Immutable user configuration
2 Input discovery
3 Environment diagnostics
4 Dependency setup and validation
5 Asset discovery and validation
6 Configuration/provenance validation
7 Tiny dual-GPU dry run
8 Runtime calibration
9 Full parallel execution
10 Merge and validation
11 Atomic output ZIP
12 Local handoff
```

---

# 8. Dependency closure

Create or validate:

```text
requirements/kaggle-base.lock
requirements/kaggle-preflight.lock
requirements/kaggle-generation.lock
requirements/kaggle-features.lock
requirements/kaggle-constraints.txt
```

Cover the actual versions used for:

- Python;
- PyTorch;
- torchvision;
- NumPy;
- SciPy;
- Pillow;
- pandas;
- PyYAML;
- jsonschema;
- safetensors;
- huggingface-hub;
- transformers;
- diffusers;
- accelerate;
- tqdm;
- packaging;
- scikit-learn when required;
- the selected CLIP loader.

Support:

```text
KAGGLE_INTERNET_ON_INSTALL
PRIVATE_WHEELHOUSE_OFFLINE
USE_PREINSTALLED_VALIDATED
```

Every notebook must run `python -m pip check` and produce:

```text
dependency_report.json
dependency_freeze.txt
pip_check.txt
```

Locally verify:

- all notebook imports are declared;
- all worker imports are declared;
- stage ZIPs contain the correct lock files;
- no conflicting pins;
- optional dependencies are not forced into the minimum pilot.

No local dependency test may download packages.

---

# 9. Asset closure

Create or validate an asset registry with:

```text
asset_id
provider
repository_or_mount
revision
expected_files
expected_hashes
license_status
redistribution_allowed
public_archive_included
private_mount_required
internet_required
loader
```

For CLIP:

```text
public archive excludes weights
private mount or user-provided validated cache required
```

Create:

```text
KAGGLE_ASSET_SETUP.md
```

with exact Kaggle mount instructions.

Absent assets must fail early with a clear blocker.

---

# 10. Execute every available CPU stage

Operate as a state machine.

At each step:

1. query readiness;
2. inspect registered artifacts;
3. execute all available CPU actions;
4. validate outputs;
5. register outputs;
6. query the next action;
7. continue while the next action is local CPU;
8. stop only at a true reference or Kaggle boundary.

Use:

```bash
python3 -m certgen readiness --explain --json
python3 -m certgen next-action --explain
python3 -m certgen doctor --json
python3 -m certgen kaggle next --explain
```

These commands must agree.

---

# 11. CIFAR handling

Look for:

```text
data/sources/cifar-10-python.tar.gz
```

If absent:

- do not download it;
- complete all independent static work;
- build all static packages that truthfully do not require it;
- stop with `PHASE1_COMPLETE_WAITING_FOR_REFERENCE`;
- print the exact expected path and validation command.

If present:

1. compute size and SHA-256;
2. validate with the canonical CLI;
3. inspect the validation report;
4. materialize the reference;
5. validate row count, IDs, hashes, and lineage;
6. register the source and materialization.

Expected pattern:

```bash
python3 -m certgen validate reference \
  --source data/sources/cifar-10-python.tar.gz \
  --explain
```

Use the exact live command.

---

# 12. Freeze the prospective study

When reference materialization exists:

- select `cifar_integrity_minimal`;
- freeze the study;
- freeze the 1k/10k/50k scale plan;
- freeze the sensitivity plan;
- freeze the runtime plan;
- build the reference draw;
- validate non-overlap;
- validate null and obvious-gap allocations;
- validate provenance;
- validate replay;
- run the paper firewall.

Do not activate DINO, CFM, second benchmark, 10k, or 50k prematurely.

---

# 13. Build all truthful static Kaggle inputs

Use:

```text
artifacts/cvpr/kaggle_inputs/
```

Subdirectories:

```text
diagnostic/
preflight/
generation/
features/
fixture_only/
```

Build and validate now:

```text
artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip
artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip
```

Each must contain:

- deterministic members;
- external manifest and SHA-256;
- package type;
- schema versions;
- source-code hash;
- study/profile hashes where applicable;
- dependency lock;
- worker contract;
- expected output schema;
- validation commands;
- upload/run/import instructions;
- no credentials;
- no restricted weights;
- no fixture payload.

For generation and features create complete blocked plans:

```text
artifacts/cvpr/kaggle_inputs/generation/BUILD_PLAN.json
artifacts/cvpr/kaggle_inputs/generation/EXPECTED_CONTENTS.json
artifacts/cvpr/kaggle_inputs/generation/README_BLOCKED.md

artifacts/cvpr/kaggle_inputs/features/BUILD_PLAN.json
artifacts/cvpr/kaggle_inputs/features/EXPECTED_CONTENTS.json
artifacts/cvpr/kaggle_inputs/features/README_BLOCKED.md
```

Do not create fake real generation or feature ZIPs.

---

# 14. Runtime guide and launchboard

Create:

```text
reports/CERTGEN_KAGGLE_RUNTIME_ESTIMATES.csv
reports/CERTGEN_KAGGLE_RUNTIME_ASSUMPTIONS.md
CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md
CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md
CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md
```

Use planning estimates:

```text
Environment diagnostic: 5–20 min
Preflight: 20–60 min
Two-model 1k generation: 45–180 min
All-role Inception + CLIP extraction: 45–180 min
Kaggle packaging per stage: 5–25 min
Local import per returned ZIP: 2–20 min
Complete first 1k pilot: 5–10 hr typical
```

Label them:

```text
PLANNING_ESTIMATE_NOT_MEASURED
```

The launchboard must be generated from artifacts and include:

```text
stage
status
input ZIP
ZIP hash
notebook
accelerator
internet setting
private assets
estimated runtime
expected output ZIP
local copy-back path
exact resume command
```

---

# 15. CPU autorun orchestrator

Create or harden:

```text
scripts/run_all_available_cpu_stages.py
commands/cpu/run_all_available_cpu_stages.sh
```

It must be:

- CPU-only;
- state-aware;
- idempotent;
- resumable;
- validation-first;
- capable of importing valid returned Kaggle outputs;
- capable of building the next real upload ZIP;
- capable of stopping at the correct external boundary;
- incapable of promoting fixtures;
- fully logged.

Support:

```bash
python3 scripts/run_all_available_cpu_stages.py --dry-run --explain
python3 scripts/run_all_available_cpu_stages.py --resume --explain
```

Exit codes:

```text
0  CPU_AVAILABLE_STAGES_COMPLETE
10 WAITING_FOR_REFERENCE
11 WAITING_FOR_KAGGLE_DIAGNOSTIC
12 WAITING_FOR_KAGGLE_PREFLIGHT
13 WAITING_FOR_KAGGLE_GENERATION
14 WAITING_FOR_KAGGLE_FEATURES
20 SCIENTIFIC_GATE_FAILED
30 LOCAL_DEFECT
```

---

# 16. Complete fixture rehearsal

Using isolated fixture paths and actual builders, prove:

```text
diagnostic input
→ fake diagnostic output
→ import
→ preflight input
→ fake preflight output
→ import
→ generation input
→ fake dual-GPU generation output
→ import
→ controls
→ feature input
→ fake dual-GPU feature output
→ import
→ cache merge
→ gates
→ all certificates
→ ranking
```

No shortcut artifacts.

Negative tests:

- zero GPU;
- one GPU;
- ambiguous input ZIP;
- dependency conflict;
- missing asset;
- stale worker marker;
- duplicate/missing seed;
- duplicate/missing feature row;
- changed study hash;
- partial ZIP;
- ZIP traversal;
- corrupt multipart output;
- fixture in real path.

---

# 17. Final Phase 1 audits

Run:

```bash
python3 -m certgen audit kaggle-launch --explain --json
python3 -m certgen audit cpu-execution --explain --json
```

If missing, implement narrowly.

Verify:

- all local-safe checks pass;
- CPU-only policy respected;
- all currently runnable CPU stages completed;
- diagnostic ZIP validates;
- preflight ZIP validates;
- generation builder is ready;
- feature builder is ready;
- all four notebooks exist;
- notebook generation is deterministic;
- dependency locks exist;
- imports are covered;
- assets fail closed;
- T4×2 split logic passes;
- resume passes;
- output ZIP logic passes;
- runtime estimates are planning-only;
- launchboard paths resolve;
- no fixture occupies a real path;
- no local defect remains;
- readiness, next-action, doctor, and kaggle-next agree.

---

# 18. Required outputs

Create:

```text
CERTGEN_PHASE1_PRE_GPU_COMPLETION_REPORT.md
CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md
CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md
CERTGEN_KAGGLE_INPUT_BUNDLE_CATALOG.md
CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md
CERTGEN_PHASE1_NEXT_ACTION.md

reports/CERTGEN_PHASE1_BASELINE.md
reports/CERTGEN_PHASE1_COMMAND_LEDGER.csv
reports/CERTGEN_PHASE1_CURRENT_STATE.json
reports/CERTGEN_PHASE1_TEST_MATRIX.md
reports/CERTGEN_PHASE1_ARTIFACT_INVENTORY.csv
reports/CERTGEN_KAGGLE_RUNTIME_ESTIMATES.csv
reports/CERTGEN_KAGGLE_RUNTIME_ASSUMPTIONS.md
reports/CERTGEN_KAGGLE_FINAL_LAUNCH_AUDIT.md
```

---

# 19. Final report

Answer:

1. Was CIFAR found?
2. Was it validated and materialized?
3. Was the profile/study frozen?
4. Was the reference draw built?
5. Which upload ZIPs now exist?
6. Which ZIPs remain stage-dependent?
7. Which notebook is next?
8. Is T4×2 required?
9. What internet mode is required?
10. Which private assets are required?
11. What is the estimated runtime?
12. What output ZIP should be downloaded?
13. Where should it be placed?
14. What exact resume command should be run?
15. Does any local defect remain?

Choose exactly one:

```text
PHASE1_COMPLETE_WAITING_FOR_REFERENCE
PHASE1_COMPLETE_WAITING_FOR_KAGGLE_DIAGNOSTIC
PHASE1_COMPLETE_WAITING_FOR_KAGGLE_PREFLIGHT
PHASE1_LOCAL_DEFECT_REMAINS
```

After success, do not recommend another speculative pre-GPU build. Print the exact next reference or Kaggle action.

Begin now.
