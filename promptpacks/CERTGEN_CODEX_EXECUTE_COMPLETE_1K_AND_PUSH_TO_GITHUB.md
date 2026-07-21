# CERTGEN — EXECUTE FROM RESTORED CIFAR TO COMPLETE 1K PILOT

You are GPT-5.6 Codex operating as a senior research-software engineer, secure artifact importer, Kaggle T4×2 execution engineer, statistical-inference auditor, reproducibility reviewer, and evidence-integrity gatekeeper.

Repository:

```text
/Users/saketmaganti/Projects/certGen
```

Required GitHub remote:

```text
https://github.com/Saket-Maganti/certgen.git
```

Required publication branch:

```text
main
```

The official CIFAR-10 Python archive has already been restored to the repository.

Your task is to execute **all currently available work**, repair only concrete defects encountered, prepare the next real Kaggle T4×2 stage, continue automatically whenever valid returned Kaggle ZIPs are present, and **commit and push every valid source-controlled project change to the user's GitHub repository at the end of each successful pass**.

This prompt is reusable. Run it again after every Kaggle output ZIP is copied back into the repository.

Do not ask which stage is active when repository state and package metadata determine it.

---

# 1. Current project assumptions

The repository previously reported:

```text
282 passed, 4 deselected
4 integration audits passed
CVPR audit 8/8
forensic audit 8/8
V9 audit 22/22
canonical release archive verified
claim_allowed=false
```

Treat those as historical reports only.

Reproduce the current live state before trusting them.

The official CIFAR archive is expected at:

```text
/Users/saketmaganti/Projects/certGen/data/sources/cifar-10-python.tar.gz
```

If it is elsewhere inside the repository, locate it safely and normalize it to the canonical path without deleting the original until validation passes.

---

# 2. Final objective

Proceed through this state machine:

```text
CIFAR validation
→ reference materialization
→ study/profile/reference-draw freeze
→ Kaggle environment diagnostic handoff
→ diagnostic import
→ Kaggle model/extractor preflight handoff
→ preflight import
→ Kaggle 1k generation handoff
→ generation import
→ CPU control construction
→ Kaggle Inception + CLIP feature extraction handoff
→ feature import
→ cache-v2 validation
→ metric and sanity gates
→ confirmatory family freeze
→ all confirmatory certificates
→ certified partial ranking
→ cross-feature analysis
→ provenance, replay, accounting, paper firewall
→ final 1k pilot report
```

The eventual successful terminal status is:

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

Perform every available local action in this run.

---

# 3. Truthfulness and evidence boundary

Until validated real execution permits otherwise:

```text
claim_allowed=false
no_fake_results=true
no_empirical_claims=true
```

Do not:

- run Kaggle or Colab locally;
- initialize CUDA locally;
- fabricate generated images, features, metrics, certificates, rankings, or runtimes;
- place fixtures in real artifact paths;
- weaken validators or thresholds to force a pass;
- modify frozen seeds, models, features, budgets, thresholds, or hypotheses after observing outcomes;
- treat tests, audits, notebooks, preflight images, or fixture runs as empirical evidence;
- certify FID or polynomial KID without a separate valid proof;
- unlock broad paper claims from a single 1k CIFAR pilot;
- start 10k, 50k, DINO, CFM, a second benchmark, or another feature family without an explicit frozen stop/go decision.

Allowed:

- CPU-only validation and repair;
- reference materialization;
- study freezing;
- Kaggle bundle construction;
- secure import of real Kaggle returns;
- real CPU metric, certificate, ranking, and reporting stages after valid feature import;
- isolated fixture-only rehearsals.

Every fixture artifact must include:

```text
synthetic_validation_only
not_real_kaggle_input
not_real_kaggle_output
not_empirical_evidence
claim_allowed=false
```

---

# 4. CPU-only policy

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
- write into canonical real-output paths;
- mutate valid immutable real artifacts.

Unexpected CUDA use or hidden network dependency is a defect.

---

# 5. Preserve repository state

Before changes:

- record current UTC time;
- record Git branch and HEAD if `.git` exists;
- record `git status --short`;
- preserve all user changes;
- do not reset, clean, rebase, or discard work;
- do not delete the CIFAR source archive;
- do not delete returned Kaggle ZIPs;
- do not overwrite immutable valid artifacts without content-hash justification;
- quarantine invalid packages instead of deleting them;
- preserve raw returned ZIPs after import.

Create or update:

```text
reports/CERTGEN_EXECUTION_BASELINE.md
reports/CERTGEN_EXECUTION_CURRENT_STATE.json
reports/CERTGEN_EXECUTION_COMMAND_LEDGER.csv
reports/CERTGEN_EXECUTION_COMMAND_LEDGER.jsonl
reports/CERTGEN_EXECUTION_ARTIFACT_INVENTORY.csv
```

Each command entry must include:

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

# 6. Discover the live CLI

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

Do not invent unsupported commands or flags.

If a required command is missing, repair it narrowly over existing builders and registries rather than adding a parallel architecture.

---

# 7. Reproduce the live baseline

Run unique local-safe checks:

- compileall;
- imports;
- canonical one-process full pytest suite;
- explicit integration audits once;
- relevant statistical tests;
- artifact-contract tests;
- post-cache tests;
- runtime-hardening tests;
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
- changed-code mypy;
- full mypy debt comparison;
- notebook deterministic-regeneration check;
- privacy scan;
- secrets scan;
- restricted-asset scan;
- release scan;
- paper compilation;
- final pre-run audit;
- maximum-ceiling audit;
- CPU-execution audit;
- Kaggle-launch audit;
- `git diff --check`.

Do not repeatedly run the same full suite.

Historical mypy debt may remain only if:

- changed-code mypy is clean;
- debt does not increase;
- the remaining count is documented.

If a concrete defect appears, repair it and add regression coverage.

Do not perform speculative upgrades.

---

# 8. Confirm the scientific contract

Before claim-bearing execution, verify the repository uses:

```text
null controls = mandatory sanity diagnostics
obvious-gap corruption controls = mandatory sanity diagnostics
controls_in_confirmatory_family = false
controls_claim_allowed = false
```

The confirmatory family must contain exactly:

```text
checkpoint/model comparison under Inception
checkpoint/model comparison under CLIP
```

Expected family size:

```text
2
```

If the live repository still includes control hypotheses in the confirmatory family, repair:

- profile/study configuration;
- family builder;
- multiplicity allocation;
- certificate-input builder;
- completeness checks;
- ranking requirements;
- cross-feature analysis;
- claim-evidence matrix;
- paper contracts;
- tests.

Preserve complete control lineage:

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

Do not treat paired clean/corrupted controls as independent confirmatory samples without a valid theorem.

---

# 9. Verify real sanity checks

Inspect current sanity implementations.

Reject hard-coded or duplicated checks such as:

```text
repeated_batching = 0.0
repeated_shard_merge = 0.0
```

Require:

## Repeated batching

Run identical ordered inputs through at least two valid batch sizes.

Compare:

- sample IDs;
- feature shape;
- dtype;
- finite values;
- maximum feature difference;
- resulting metric difference.

## Independent shard merge

Build equivalent outputs through at least:

```text
one-shard path
two-shard path
```

Compare row coverage, ordering, hashes where exact, and numerical tolerances where appropriate.

## Corruption ladder

Use clean plus at least three nonzero prospectively frozen severities for one deterministic primary corruption family.

Do not reuse one corruption result under several names.

## Nonclaim control certificates

Run the actual certificate implementation for control-code validation only.

Label:

```text
sanity_control_only
not_confirmatory_certificate
claim_allowed=false
```

If these repairs are already present, verify them and continue.

---

# 10. Validate the official CIFAR archive

Expected path:

```text
data/sources/cifar-10-python.tar.gz
```

Validate safely using the actual CertGen CLI.

Conceptually verify:

- gzip/tar structure;
- safe member paths;
- no symlinks;
- expected `cifar-10-batches-py/` members;
- `data_batch_1` through `data_batch_5`;
- `test_batch`;
- batch decoding;
- 50,000 train images;
- 10,000 test images;
- 10 classes;
- expected dimensions;
- valid labels;
- no duplicate IDs;
- archive size and SHA-256;
- source provenance.

Do not use or rename Kaggle `train.7z` or `test.7z` when this archive is available.

If missing:

```text
WAITING_FOR_REFERENCE_ARCHIVE
```

If invalid:

```text
INVALID_REFERENCE_ARCHIVE
```

Do not continue to materialization on failure.

---

# 11. Materialize the CIFAR reference

After successful validation:

- materialize the canonical reference representation;
- preserve source archive hash;
- create deterministic sample IDs;
- create source IDs;
- validate image decoding;
- validate image mode and dimensions;
- validate counts;
- validate labels as needed;
- detect duplicates or omissions;
- create the reference manifest;
- register all artifacts;
- verify content hashes;
- verify source-to-materialized lineage.

Do not use the Kaggle competition test set for the initial CertGen pilot.

---

# 12. Freeze the prospective 1k study

After reference materialization:

- select the canonical minimal CIFAR integrity profile;
- freeze the study;
- freeze the two selected checkpoint candidates;
- freeze Inception;
- freeze CLIP;
- freeze preprocessing;
- freeze bounded RBF-MMD settings;
- freeze support normalization;
- freeze RBF bandwidth rule;
- freeze generation seeds;
- freeze the 1k sample budget;
- freeze reference draw;
- freeze control allocations;
- freeze the two-hypothesis confirmatory family;
- freeze multiplicity allocation;
- freeze sanity thresholds;
- freeze stop/go rules;
- freeze planning-only runtime assumptions;
- freeze prospective sensitivity lanes.

Validate:

- reference-role non-overlap;
- intended control pairing;
- source lineage;
- hashes;
- provenance;
- deterministic replay;
- paper firewall.

Do not activate larger scales or extra models.

---

# 13. Canonical Kaggle notebooks

Ensure these active notebooks exist:

```text
notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb
notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb
```

Every notebook must:

- instruct the user to select GPU T4 ×2;
- verify two visible CUDA devices;
- use multiprocessing `spawn`;
- avoid parent CUDA initialization before spawn;
- use one active worker per GPU;
- partition ordered seeds or rows deterministically;
- validate dependencies;
- validate assets;
- preserve study/profile/configuration hashes;
- run a tiny non-evidence dual-GPU check;
- measure load time, warmup, throughput, VRAM, and safe batch size;
- support deterministic resume;
- write shards atomically;
- validate worker-contract versions;
- create status files and member hashes;
- build and revalidate one output ZIP;
- support multipart fallback;
- print exact copy-back and resume commands;
- contain no stored executed results.

Run deterministic-regeneration and static-analysis checks.

---

# 14. Dependency and asset closure

Verify actual imports and lock files for:

- diagnostic;
- preflight;
- generation;
- feature extraction;
- model workers;
- Inception loader;
- CLIP loader.

Use one actual minimal CLIP route.

If Transformers CLIP is active and `timm` or `open-clip-torch` is unused, remove them from required compatibility checks.

If they are required, add compatible versions to the appropriate lock file.

Validate:

```text
requirements/kaggle-base.lock
requirements/kaggle-preflight.lock
requirements/kaggle-generation.lock
requirements/kaggle-features.lock
requirements/kaggle-constraints.txt
```

Each Kaggle stage must produce:

```text
dependency_report.json
dependency_freeze.txt
pip_check.txt
```

Validate the asset registry for:

```text
Google DDPM CIFAR-10 checkpoint
Frank DDPM EMA CIFAR-10 checkpoint
Inception weights
CLIP weights
```

Each record must include:

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

Do not embed restricted weights in public archives.

If a private asset is absent, fail early and print the exact Kaggle setup action.

---

# 15. State-aware CPU autorun

Use or repair:

```text
scripts/run_all_available_cpu_stages.py
commands/cpu/run_all_available_cpu_stages.sh
```

Canonical invocation:

```bash
python3 scripts/run_all_available_cpu_stages.py \
  --resume \
  --explain
```

It must:

- run CPU-only;
- query actual readiness;
- discover registered artifacts;
- discover real returned Kaggle ZIPs by package metadata;
- validate them securely;
- import only valid outputs;
- execute every available local stage;
- build the next real Kaggle input ZIP;
- stop only at a true external boundary;
- continue through final CPU analysis after feature import;
- be idempotent;
- be resumable;
- never promote fixtures;
- log every action.

Readiness views must agree:

```bash
python3 -m certgen readiness --explain --json
python3 -m certgen next-action --explain
python3 -m certgen doctor --json
python3 -m certgen kaggle next --explain
```

Disagreement is a local defect.

---

# 16. Secure import of returned Kaggle ZIPs

Inspect canonical incoming locations.

Classify candidates by package metadata:

```text
DIAGNOSTIC_OUTPUT
PREFLIGHT_OUTPUT
GENERATION_OUTPUT
FEATURE_OUTPUT
NONE
AMBIGUOUS
INVALID
```

Do not classify from filename alone.

Before import:

- inspect without extraction;
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
- validate seed or row coverage;
- reject stale packages;
- reject duplicates;
- reject incomplete packages unless explicitly supported;
- reject fixture markers.

Quarantine invalid packages and preserve the exact reason.

Preserve valid raw ZIPs after import.

---

# 17. Kaggle environment diagnostic boundary

If no valid diagnostic return exists:

- build and validate the diagnostic input ZIP;
- validate the notebook;
- update the launchboard;
- stop with:

```text
WAITING_FOR_KAGGLE_DIAGNOSTIC
```

Report exactly:

```text
input ZIP
input ZIP SHA-256
notebook
accelerator GPU T4 ×2
internet mode
expected output ZIP
local copy-back path
exact resume command
```

If a valid diagnostic return exists:

- import it;
- verify two T4 GPUs;
- verify multiprocessing;
- verify disk and write access;
- verify dependency mode;
- record measured diagnostic timings;
- preserve planning estimates separately;
- continue automatically.

---

# 18. Kaggle preflight boundary

If no valid preflight return exists:

- build and validate the preflight input ZIP;
- verify asset instructions;
- verify deterministic notebook generation;
- stop with:

```text
WAITING_FOR_KAGGLE_PREFLIGHT
```

If a valid preflight return exists:

- import it;
- verify both checkpoints;
- verify Inception;
- verify CLIP;
- verify revisions and hashes;
- ingest load time;
- ingest throughput;
- ingest safe batch size;
- ingest peak VRAM;
- fail closed on required failure;
- build the real 1k generation input ZIP;
- validate it;
- create its run capsule;
- register provenance;
- verify replay;
- continue to the generation boundary.

---

# 19. Kaggle 1k generation boundary

Pilot:

```text
two selected checkpoint candidates
1,000 images per model
deterministic dual-GPU seed split
```

If no valid generation return exists:

- verify the generation input ZIP;
- verify seed plan;
- verify worker contract;
- verify the notebook;
- stop with:

```text
WAITING_FOR_KAGGLE_GENERATION
```

If a valid generation return exists:

- import it;
- validate exact model coverage;
- validate 1,000 expected images per model;
- validate complete seed coverage;
- reject duplicate or missing seeds;
- decode and validate images;
- validate dimensions and RGB mode;
- validate hashes;
- validate checkpoint identity;
- validate shard and merged manifests;
- register generated artifacts;
- verify provenance;
- verify replay;
- continue automatically to control construction.

---

# 20. Build real CPU controls

Build:

```text
deterministic null reference control
deterministic obvious-gap corruption control
```

Controls remain sanity-only.

Validate:

- source IDs;
- reference draw IDs;
- exact counts;
- intended clean/corrupt pairing;
- corruption function;
- severity;
- seeds;
- image hashes;
- manifests;
- provenance;
- no unintended overlap.

Build the frozen corruption ladder and nonclaim control-certificate inputs.

Label:

```text
sanity_control_only
not_confirmatory_certificate
claim_allowed=false
```

Then build and validate the real feature-extraction input ZIP.

---

# 21. Kaggle feature-extraction boundary

Required extractors:

```text
Inception
CLIP
```

Required roles include:

- reference;
- each generated model;
- null controls;
- corruption controls.

If no valid feature return exists:

- verify the feature input ZIP;
- verify role counts;
- verify ordered manifests;
- verify preprocessing locks;
- verify assets;
- verify deterministic row partition;
- verify the notebook;
- stop with:

```text
WAITING_FOR_KAGGLE_FEATURES
```

If a valid feature return exists:

- import it;
- validate both extractors;
- validate every role;
- verify exact row coverage;
- reject duplicate or missing rows;
- verify sample IDs;
- verify control source IDs;
- verify shapes;
- verify dtypes;
- verify finite arrays;
- verify preprocessing hashes;
- verify extractor revisions;
- verify shard manifests;
- verify deterministic merge;
- register feature artifacts;
- merge to cache-v2;
- validate caches;
- update provenance and replay.

Do not stop after feature import.

---

# 22. Run metric and sanity gates

After valid caches exist:

- freeze metric configuration;
- freeze sanity configuration;
- run point-estimate reproduction where applicable;
- run feature alignment;
- run null controls;
- run the multi-severity corruption ladder;
- run real repeated-batching checks;
- run real independent shard-merge checks;
- run nonclaim control certificates;
- validate preprocessing;
- validate bounded-kernel assumptions;
- validate support normalization;
- validate role separation;
- reject NaNs or infinities.

Do not change thresholds after seeing results.

If a required gate fails:

```text
SCIENTIFIC_GATE_FAILED
```

Preserve:

- exact failure;
- diagnostics;
- artifacts;
- rerun frontier;
- whether the defect is data, feature extraction, preprocessing, metric, or theory.

Do not proceed to confirmatory certificates.

---

# 23. Freeze and execute the confirmatory family

After gates pass, freeze exactly:

```text
checkpoint/model comparison under Inception
checkpoint/model comparison under CLIP
```

Validate:

- family size = 2;
- unique hypothesis IDs;
- alpha allocation;
- budgets;
- feature definitions;
- model roles;
- reference role;
- kernel settings;
- reference-draw identity;
- no controls in the family;
- no missing or extra bundles.

Build and validate every certificate-input bundle.

Execute every missing certificate.

Do not stop after the first.

Reuse completed certificates only when all content and parent hashes match.

Verify:

- time-uniform method;
- bounded-stream assumptions;
- alpha allocation;
- first crossing;
- decision direction;
- samples to decision;
- unresolved censoring;
- maximum budget;
- lineage;
- complete family coverage.

Label 1k results:

```text
pilot_only
single_benchmark_only
not_generalized
```

Do not unlock broad claims.

---

# 24. Ranking and cross-feature analysis

Require complete confirmatory coverage or prospectively frozen exclusions.

Build a certified partial ranking.

Do not force a total order.

Produce:

```text
ranking_graph.json
ranking_edges.csv
ranking_unresolved.csv
ranking_invalid.csv
ranking_provenance.json
```

Every edge must link to supporting certificates.

Produce cross-feature outputs:

```text
agreement_matrix.csv
direction_disagreements.csv
decided_vs_unresolved.csv
invalid_feature_lanes.csv
consensus_edges.json
representation_specific_edges.json
```

Classify:

```text
agreement
representation-specific result
unresolved
invalid
```

Do not call Inception/CLIP disagreement an implementation defect unless contracts fail.

---

# 25. Final accounting and evidence closure

Complete:

- CPU duration records;
- imported Kaggle duration records;
- model load time;
- generation GPU seconds;
- feature GPU seconds;
- merge time;
- certificate time;
- first-decision sample count;
- maximum sample count;
- retrospective sample savings;
- disk and ZIP sizes;
- provenance DAG;
- provenance verification;
- deterministic replay;
- minimum rerun frontier;
- artifact inventory;
- claim-evidence matrix;
- paper firewall;
- figure/table contract validation;
- pilot stop/go report.

Maintain labels:

```text
PLANNING_ESTIMATE_NOT_MEASURED
MEASURED_KAGGLE_PREFLIGHT
MEASURED_REAL_RUN
DERIVED_FROM_MEASURED_RUN
```

Never present planning estimates as measured.

---

# 26. Paper policy

The paper may include only validated real pilot outputs after all required gates pass.

Do not:

- insert fixture values;
- imply multi-benchmark generality;
- claim leaderboard-wide validation;
- imply CVPR readiness from a single 1k pilot;
- certify FID;
- call controls confirmatory certificates;
- hide unresolved or invalid results.

State the exact scope:

```text
CIFAR-10
two checkpoint candidates
Inception and CLIP
1k pilot
two-hypothesis confirmatory family
controls as sanity diagnostics
```

Keep broad `claim_allowed=false`.

---

# 27. Release verification

Build a clean deterministic release archive.

Include required root files:

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
credentials
restricted/private model weights
```

Fresh-extract in a clean temporary directory and run:

- safe extraction checks;
- compileall;
- imports;
- portable tests;
- notebook validation;
- privacy scan;
- restricted-asset scan;
- paper firewall;
- manifest verification.

Record:

```text
archive path
member count
size
SHA-256
fresh-extraction result
```

---


# 28. GitHub publication, commit, and push

At the end of **every successful pass**, after all applicable tests, audits, artifact checks, and release checks have completed, commit and push all valid source-controlled CertGen changes to:

```text
https://github.com/Saket-Maganti/certgen.git
```

Target branch:

```text
main
```

This applies at:

- the first CIFAR/reference preparation boundary;
- every later Kaggle boundary;
- scientific-gate failure after diagnostics are preserved;
- final 1k completion.

Do not wait until the entire multi-stage Kaggle workflow is finished to create the first backup. Each completed local pass must produce a reproducible Git checkpoint.

## 28.1 Git and GitHub prerequisites

Check:

```bash
git --version
gh --version
gh auth status
```

If `gh` is missing, do not attempt an unsafe workaround. Record:

```text
GITHUB_CLI_REQUIRED
```

If authentication is missing or invalid, record:

```text
GITHUB_AUTH_REQUIRED
```

Print the exact command the user must run:

```bash
gh auth login
```

The scientific/execution work may still finish to its truthful stage status, but GitHub publication must be reported as blocked.

Do not place credentials, tokens, or authentication output into reports or commits.

## 28.2 Initialize or normalize Git safely

Inspect:

```bash
git status -sb
git branch --show-current
git remote -v
```

If the checkout is not yet a Git repository:

```bash
git init -b main
```

If no `origin` exists:

```bash
git remote add origin https://github.com/Saket-Maganti/certgen.git
```

If `origin` already points to the required URL, preserve it.

If `origin` points elsewhere:

1. preserve the existing URL in the publication report;
2. rename the existing remote to a non-conflicting name such as `previous-origin` when safe;
3. add the required repository as `origin`;
4. do not silently discard the old remote information.

Fetch without modifying the worktree:

```bash
git fetch origin --prune
```

Determine whether `origin/main` exists.

### Empty or new remote

When the remote is empty, preserve the local project history when one exists and publish the current validated tree to `main`.

### Existing related remote history

When `origin/main` exists and shares ancestry:

- integrate safely;
- do not discard either side;
- use a normal fast-forward, rebase, or merge as appropriate;
- rerun relevant checks after conflict resolution;
- do not push until the integrated tree is valid.

### Existing unrelated or conflicting remote history

Do not force-push.

Do not use:

```bash
git push --force
git push --force-with-lease
git reset --hard origin/main
```

Record:

```text
GITHUB_REMOTE_HISTORY_CONFLICT
```

Preserve both histories and print the exact blocker.

## 28.3 Meaning of “commit everything”

Commit **all valid source-controlled project work**, including as applicable:

- source code;
- tests;
- configuration;
- schemas;
- notebooks without stored execution outputs;
- command wrappers;
- documentation;
- paper source;
- small manifests;
- provenance metadata;
- audit reports;
- execution ledgers without secrets or private paths;
- small deterministic static Kaggle bundles that contain no dataset, generated images, private weights, credentials, or restricted assets;
- release manifests;
- reproducibility metadata.

Do **not** commit raw or bulky execution inputs and outputs merely because they exist in the project directory.

The following must not be committed unless an explicit repository policy already tracks a small safe derivative:

```text
data/sources/cifar-10-python.tar.gz
raw CIFAR images or extracted dataset payloads
train.7z
test.7z
model checkpoints
Inception weights
CLIP weights
private Kaggle asset bundles
credentials
API keys
.env files containing secrets
generated model images
feature arrays and feature caches
raw returned Kaggle ZIPs
large multipart outputs
temporary extraction directories
quarantine payloads
__MACOSX
.DS_Store
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
temporary logs
```

The CIFAR archive is an execution input, not source code. It must remain available locally for execution but must not be staged or pushed.

Prefer committing:

- source hashes;
- dataset provenance;
- manifests;
- validation reports;
- role/count summaries;
- reproduction instructions;

instead of raw data.

## 28.4 Strengthen `.gitignore`

Before staging, ensure `.gitignore` protects at least:

```gitignore
# Raw datasets and source archives
data/sources/
*.7z
*.tar
*.tar.gz
*.tgz

# Private and restricted model assets
*.pth
*.pt
*.ckpt
*.safetensors
private_assets/
artifacts/**/private_assets/

# Real generated data and feature caches
data/generated/
data/features/
data/materialized/
artifacts/**/incoming/
artifacts/**/returned/
artifacts/**/generated/
artifacts/**/features/
artifacts/**/cache*/
artifacts/**/raw_outputs/
artifacts/**/quarantine/

# Secrets
.env
.env.*
*.pem
*.key
credentials*
secrets*

# Local caches and operating-system files
__MACOSX/
.DS_Store
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

Do not blindly ignore a directory containing intentionally tracked source code or small canonical schemas. Inspect existing repository conventions and make narrow exceptions where necessary.

If a prohibited large/private file is already tracked:

- do not merely add it to `.gitignore`;
- remove it from the Git index with `git rm --cached` while keeping the local file;
- verify that the working file remains available;
- record the repair.

Do not rewrite published Git history without explicit user authorization.

## 28.5 Secret, privacy, and large-file gate

Before staging, run:

- repository secrets scan;
- privacy scan;
- restricted-asset scan;
- absolute-path scan;
- large-file inventory.

Create:

```text
reports/CERTGEN_GIT_LARGE_FILE_AUDIT.csv
reports/CERTGEN_GITHUB_PUBLICATION_REPORT.md
reports/CERTGEN_GITHUB_PUSH_LEDGER.jsonl
```

The large-file audit must include:

```text
path
size_bytes
tracked
ignored
lfs_managed
classification
allowed_to_commit
reason
```

Block staging of any non-LFS file at or above:

```text
90 MiB
```

This margin is intentionally below GitHub's 100 MiB hard file limit.

Do not automatically introduce Git LFS for raw datasets, generated images, feature caches, or private weights. Those artifacts belong in external storage or reproducible Kaggle bundles, not the source repository.

If a legitimate source-controlled file exceeds the limit:

```text
GITHUB_LARGE_FILE_BLOCKED
```

Report it instead of attempting a partial or forceful push.

## 28.6 Review the complete intended diff

Because the user explicitly requested all valid project changes to be committed, staging may use:

```bash
git add -A
```

only **after**:

- `.gitignore` is correct;
- secrets scan passes;
- private/restricted asset scan passes;
- large-file scan passes;
- raw CIFAR is confirmed untracked;
- returned Kaggle outputs are confirmed untracked;
- the complete worktree has been inspected.

Before committing, record:

```bash
git status --short
git diff --stat
git diff --check
git diff --cached --stat
```

Inspect the staged file list.

Fail if the staged set includes:

- CIFAR archive or extracted raw dataset;
- model/extractor weights;
- generated images;
- feature caches;
- raw Kaggle returns;
- credentials;
- absolute private paths that should be portable;
- temporary or operating-system files.

## 28.7 Commit policy

Create one intentional commit for the current completed pass.

Use a concise stage-aware subject.

Examples:

```text
Prepare CertGen CIFAR reference and Kaggle diagnostic
Advance CertGen to Kaggle preflight
Advance CertGen to 1k generation
Advance CertGen to feature extraction
Record CertGen scientific gate diagnostics
Complete CertGen 1k pilot
```

The commit body must summarize:

- completed execution stage;
- important repairs;
- tests and audits run;
- exact stage status;
- evidence boundary;
- next external action.

Do not claim empirical completion when waiting at a Kaggle boundary.

Do not create an empty commit unless needed to record a meaningful externally completed stage and the user explicitly requested it.

## 28.8 Push policy

After the commit:

```bash
git push -u origin HEAD:main
```

Use normal non-force push only.

If remote integration is needed, resolve it safely and rerun checks before pushing.

After pushing, verify:

```bash
git rev-parse HEAD
git ls-remote origin refs/heads/main
git status -sb
```

Require the local HEAD and remote `main` commit to agree.

Record:

```text
remote_url
branch
commit_sha
commit_subject
push_start_utc
push_end_utc
remote_verified
working_tree_status
```

Publication success status:

```text
GITHUB_PUSHED_AND_VERIFIED
```

Possible publication blockers:

```text
GITHUB_CLI_REQUIRED
GITHUB_AUTH_REQUIRED
GITHUB_REMOTE_HISTORY_CONFLICT
GITHUB_LARGE_FILE_BLOCKED
GITHUB_SECRET_SCAN_FAILED
GITHUB_PUSH_FAILED
```

A GitHub publication blocker must not be mislabeled as a scientific failure.

## 28.9 Final completion tag

Only after:

```text
FULL_1K_CPU_ANALYSIS_COMPLETE
```

and after the final commit is pushed, create an annotated tag:

```text
certgen-1k-pilot-complete
```

Tag message:

```text
CertGen validated 1k pilot completion
```

Do not move or overwrite an existing tag.

Push it normally:

```bash
git push origin certgen-1k-pilot-complete
```

Verify the remote tag.

Do not create this tag at an intermediate Kaggle boundary.

## 28.10 GitHub publication is mandatory at the end of each pass

Do not finish a successful pass without attempting the safe commit-and-push workflow.

The final response must clearly separate:

```text
EXECUTION_STATUS
GITHUB_PUBLICATION_STATUS
```

The scientific/execution status remains one of the canonical stage statuses.

The GitHub publication status must be one of the publication statuses listed above.


# 29. Required outputs

Create or update:

```text
CERTGEN_EXECUTION_AND_HANDOFF_REPORT.md
CERTGEN_CURRENT_NEXT_ACTION.md
CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md
CERTGEN_KAGGLE_T4X2_EXECUTION_HANDBOOK.md
CERTGEN_KAGGLE_INPUT_BUNDLE_CATALOG.md
CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md
CERTGEN_1K_PILOT_FINAL_EXECUTION_REPORT.md
CERTGEN_1K_PILOT_STOP_GO_REPORT.md

reports/CERTGEN_EXECUTION_BASELINE.md
reports/CERTGEN_EXECUTION_CURRENT_STATE.json
reports/CERTGEN_EXECUTION_COMMAND_LEDGER.csv
reports/CERTGEN_EXECUTION_COMMAND_LEDGER.jsonl
reports/CERTGEN_EXECUTION_ARTIFACT_INVENTORY.csv
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
reports/CERTGEN_GIT_LARGE_FILE_AUDIT.csv
reports/CERTGEN_GITHUB_PUBLICATION_REPORT.md
reports/CERTGEN_GITHUB_PUSH_LEDGER.jsonl
```

At each Kaggle boundary, the handoff must contain:

```text
completed stage
next notebook
input ZIP
input ZIP SHA-256
accelerator
internet mode
private assets
estimated runtime
expected output ZIP
local copy-back path
exact resume command
```

---

# 30. Final response requirements

Answer:

1. Was the CIFAR archive found?
2. Was it valid?
3. Was it materialized?
4. Did the full one-process test suite pass?
5. Were all relevant audits clean?
6. Was the study frozen?
7. Is the confirmatory family exactly two hypotheses?
8. Are controls sanity-only?
9. Which Kaggle input ZIPs exist?
10. Which returned Kaggle ZIP was found, if any?
11. Was it valid and imported?
12. Which CPU stages ran?
13. Which next input ZIP was built?
14. Which notebook is next?
15. What accelerator is required?
16. What internet/private-asset mode is required?
17. What output ZIP must be downloaded?
18. Where must it be copied locally?
19. What exact resume command must be run?
20. If features were imported, did all gates pass?
21. Were both confirmatory certificates completed?
22. Was the partial ranking built?
23. Was cross-feature analysis completed?
24. Are claims still blocked or narrowly unlocked?
25. Does any local defect remain?
26. Was every valid source-controlled project change committed?
27. What Git branch was pushed?
28. What is the commit SHA?
29. Does `origin` point to `https://github.com/Saket-Maganti/certgen.git`?
30. Does remote `main` match local HEAD?
31. Was the final completion tag created, when applicable?
32. What is the GitHub publication status?
33. What is the exact execution status?

Report both:

```text
EXECUTION_STATUS=<one canonical execution status>
GITHUB_PUBLICATION_STATUS=<one canonical publication status>
```

Choose exactly one execution status:

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

Choose exactly one GitHub publication status:

```text
GITHUB_PUSHED_AND_VERIFIED
GITHUB_CLI_REQUIRED
GITHUB_AUTH_REQUIRED
GITHUB_REMOTE_HISTORY_CONFLICT
GITHUB_LARGE_FILE_BLOCKED
GITHUB_SECRET_SCAN_FAILED
GITHUB_PUSH_FAILED
```

At a Kaggle boundary, do not recommend another prompt.

Print the one exact next action.

After `FULL_1K_CPU_ANALYSIS_COMPLETE`, do not expand automatically. Report the frozen stop/go decision and wait for explicit authorization.

Begin now by preserving repository state, discovering the actual CLI, reproducing the current baseline, validating the restored CIFAR archive, executing every currently available CPU stage, and finally committing and pushing every valid source-controlled change to `https://github.com/Saket-Maganti/certgen.git`.
