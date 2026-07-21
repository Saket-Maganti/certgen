# CERTGEN — FINAL 100% PRE-RUN READINESS SEAL, CERTIFICATE-HANDOFF CLOSURE, CONTROL-BUILDER COMPLETION, AND CVPR VALUE MAXIMIZATION

You are GPT‑5.6 Sol operating as:

- a senior computer-vision researcher;
- a generative-model evaluation researcher;
- a sequential-inference specialist;
- a research software architect;
- a Kaggle T4×2 execution engineer;
- a reproducibility and artifact-integrity auditor;
- a CVPR reviewer focused on scientific value and real execution continuity.

You have full access to the live repository:

```text
/Users/saketmaganti/Projects/certGen
```

Your task is to perform the **last pre-run engineering pass** for CertGen.

This is the final closure contract.

Do not create another version layer.

Do not create V10/V11/V12/V13 prompt packs.

Do not add another parallel pipeline.

Do not broaden the project into new theory, video, dashboards, web apps, cloud orchestration, or manuscript automation.

Work directly on the canonical CVPR pipeline and close every remaining local handoff defect between:

```text
reference materialization
→ frozen reference draw plan
→ real preflight
→ generation
→ feature extraction
→ cache-v2 merge
→ control construction
→ certificate-input construction
→ frozen multiplicity family
→ certificate execution
→ partial ranking
→ cross-feature analysis
→ paper evidence gating
```

The repository must finish this pass in a state where:

> Every locally implementable and locally testable pre-run requirement is complete. The only remaining blockers are real user-provided reference data, real Kaggle model/extractor preflight, real generation, real feature extraction, real metric results, real certificates, and real empirical paper evidence.

The final acceptable status is:

```text
CVPR_100_PERCENT_PRE_RUN_READY
BLOCKED_ONLY_BY_REAL_INPUTS_AND_REAL_EXECUTION
```

This does **not** mean the project has real evidence or is publication-ready.

It means the code, builders, schemas, notebooks, imports, controls, certificate inputs, analysis contracts, release package, and execution instructions are fully ready before real runs.

Do not claim “100% ready” unless every completion gate in this prompt passes.

---

# 1. Current verified state

The project already contains:

- bounded RBF-MMD comparison logic;
- union-Hoeffding time-uniform confidence sequences;
- Bonferroni family-wise control;
- evidence and paper firewalls;
- model and extractor preflight infrastructure;
- Kaggle T4×2 notebooks;
- one-worker-per-GPU queueing;
- model-family adapters;
- Inception and CLIP adapter work;
- pilot profile selection;
- unified image manifests;
- embedded feature-image packaging;
- secure importers;
- feature merge into cache-v2;
- partial-ranking infrastructure;
- cross-feature analysis contracts;
- runtime planning;
- synthetic runtime tests;
- portable release packaging.

The latest audit found that the front half of the pipeline is credible, but the late-stage execution path still has seven concrete gaps:

1. worker-version mismatch in resume markers;
2. no canonical reference draw-plan builder;
3. no canonical control-artifact builder;
4. no canonical certificate-input bundle builder;
5. next-action commands use hardcoded or nonexistent paths;
6. portable-versus-live verification reporting is conflated;
7. CLIP cache redistribution policy is not explicit enough.

This pass must close those issues completely and verify the entire real contract end to end using fixture data and the actual builders.

---

# 2. Scientific boundary

The rigorous claim-bearing route remains:

- fixed prospective benchmark and model membership;
- fixed reference population and draw protocol;
- fixed feature definitions and preprocessing;
- bounded RBF-MMD difference stream;
- non-overlapping sample roles;
- time-uniform union-Hoeffding confidence sequence;
- first-crossing directional decision;
- Bonferroni simultaneous family control;
- certified partial rankings;
- unresolved does not mean equivalent;
- FID/FD remain descriptive unless separately justified;
- polynomial KID is not automatically certified;
- no metric-agnostic guarantee;
- no empirical claim before real evidence.

Do not weaken or broaden this boundary.

---

# 3. Non-negotiable restrictions

Do not:

- download CIFAR;
- download large model checkpoints during local tests;
- run Kaggle;
- run Colab;
- require CUDA in local tests;
- perform real generation;
- perform real feature extraction;
- run real claim-bearing certificates;
- fabricate metrics;
- fabricate runtime results;
- populate paper results;
- set `claim_allowed=true`;
- fabricate model or dataset licenses;
- claim Kaggle success without a real Kaggle run.

Allowed:

- fixture datasets;
- fake model and extractor adapters;
- synthetic images;
- synthetic features;
- local CPU tests;
- package and archive generation;
- notebook static analysis;
- secure import tests;
- builder-faithful end-to-end synthetic execution;
- paper compilation;
- release verification.

All fixture outputs must be labeled:

```text
synthetic_validation_only
not_empirical_evidence
claim_allowed=false
```

---

# 4. Required workflow

Work in this order:

1. inspect the live repository;
2. reproduce the complete baseline;
3. verify each remaining gap;
4. implement shared canonical contracts;
5. repair all builders and next-action paths;
6. run the exact real builders through fixture artifacts;
7. regenerate notebooks and documentation;
8. run the complete local-safe test and audit matrix;
9. build and validate the portable archive;
10. issue one final readiness status;
11. issue one exact next command;
12. explicitly state that no further pre-run patch is justified.

For every finding classify:

```text
CONFIRMED
ALREADY_FIXED
PARTIALLY_FIXED
NOT_REPRODUCED
NEW_DEFECT
BLOCKED_ONLY_BY_REAL_EXECUTION
```

---

# 5. Phase A — Baseline reproduction

Run and record:

- Python compilation;
- package imports;
- full non-recursive default pytest;
- integration-audit lane;
- statistical lane;
- artifact-contract lane;
- runtime-hardening lane;
- real-execution-closure lane;
- final run-ready closure lane;
- notebook static analyzer;
- deterministic notebook regeneration;
- CVPR audit;
- forensic audit;
- V9 compatibility audit;
- paper firewall;
- privacy scan;
- release scan;
- Ruff;
- critical mypy;
- full mypy debt comparison;
- paper compilation;
- `git diff --check`.

Create:

```text
reports/CERTGEN_FINAL_100_PERCENT_BASELINE.md
reports/CERTGEN_FINAL_100_PERCENT_COMMAND_LEDGER.csv
reports/CERTGEN_FINAL_100_PERCENT_CURRENT_STATE.json
```

Every command record must include:

```text
command
cwd
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

---

# 6. Phase B — Canonical worker-version contract

Create one shared constant and schema for worker identity.

Preferred location:

```text
certgen/notebooks/worker_contract.py
```

Required fields:

```text
worker_contract_version
worker_type
worker_implementation_version
config_schema_version
output_schema_version
```

All of these must consume the same source of truth:

- preflight workers;
- extractor-preflight workers;
- generation workers;
- feature workers;
- `WorkerSpec`;
- completion markers;
- resume validation;
- notebook generation;
- importers;
- tests.

Do not hardcode `v2` in one place and `v3` in another.

Completion-marker validation must fail only on a real incompatibility.

Add tests for:

- exact version match;
- old compatible version;
- incompatible version;
- missing version;
- stale marker;
- mixed worker types.

---

# 7. Phase C — Canonical reference draw-plan builder

Add:

```bash
python3 -m certgen prepare reference-draw \
  --profile <profile> \
  --study <frozen-study>
```

The builder must consume:

- materialized reference manifest;
- frozen study hash;
- selected pilot profile;
- reference population hash;
- sample budget;
- seed;
- replacement policy;
- role definitions;
- control requirements.

Output:

```text
registry/manifests/cvpr/reference_draw_plan.json
```

Required fields:

```text
draw_plan_id
study_hash
profile_id
benchmark_id
reference_population_hash
draw_method
with_or_without_replacement
seed
ordered_reference_ids
time_index
roles
non_overlap_constraints
control_allocations
configuration_hash
created_at
claim_allowed
```

The builder must support:

- model-comparison reference role;
- null-control split A;
- null-control split B;
- obvious-gap clean role;
- obvious-gap corrupted role;
- future additional prospectively frozen controls.

The draw plan must be deterministic and idempotent.

Reject:

- missing reference manifest;
- duplicate IDs where forbidden;
- insufficient reference population;
- unfrozen study;
- changed study hash;
- changed profile;
- post hoc role insertion.

Add exact CLI documentation and next-action integration.

---

# 8. Phase D — Canonical control-artifact builder

Add:

```bash
python3 -m certgen prepare controls \
  --study <frozen-study> \
  --reference-draw <draw-plan>
```

The control builder must create all claim-bearing control inputs required by the selected family.

At minimum:

## 8.1 Null control

Construct deterministic:

```text
reference_split_a
reference_split_b
shared_or_independent_reference_role as required by the theorem
```

Record:

```text
sample IDs
role IDs
draw positions
hashes
non-overlap validation
```

## 8.2 Obvious-gap control

Construct one deterministic corruption protocol.

The protocol must freeze:

```text
corruption type
severity
parameters
seed
input sample IDs
output sample IDs
output hashes
image dimensions
color mode
```

Examples may include:

- Gaussian blur;
- additive noise;
- JPEG degradation;
- resize degradation.

Choose one primary obvious-gap control for the minimum pilot and document why.

Do not tune severity after seeing certificate outcomes.

## 8.3 Control output package

Produce:

```text
artifacts/cvpr/controls/<study_hash>/
    null_control_manifest.json
    obvious_gap_manifest.json
    clean_images/
    corrupted_images/
    integrity_manifest.json
    status.json
```

All control artifacts before real feature extraction remain:

```text
planning_or_input_artifact
claim_allowed=false
```

## 8.4 Control feature integration

The feature-package builder must include control images and roles in the selected extractor lanes.

The feature merge must preserve control role labels.

---

# 9. Phase E — Canonical certificate-input bundle builder

Add:

```bash
python3 -m certgen prepare certificate-inputs \
  --study <frozen-study> \
  --family <family-id> \
  --feature-run <run-id>
```

This builder must consume:

- frozen study;
- frozen family;
- reference draw plan;
- validated cache-v2 artifacts;
- merged role manifests;
- control manifests;
- artifact registry.

Produce one immutable bundle per claim-bearing hypothesis.

Required bundle fields:

```text
comparison_id
family_id
study_hash
feature_space
metric
kernel
bandwidth
budget
model_a
model_b
features_a
features_b
features_r
sample_ids_a
sample_ids_b
source_ids_r
role_manifest_hash
reference_draw_hash
feature_cache_hashes
preprocessing_hash
extractor_hash
alpha_total
alpha_hypothesis
configuration_hash
evidence_class
claim_allowed
```

Preferred output layout:

```text
artifacts/cvpr/certificate_inputs/<study_hash>/<family_id>/<comparison_id>/<feature_space>/
    certificate_inputs.npz
    sidecar.json
    validation.json
```

The builder must support:

- generated-model comparison;
- null reference-split comparison;
- obvious-gap clean-versus-corrupt comparison.

Reject:

- missing role;
- mixed preprocessing;
- mixed extractor revision;
- missing sample IDs;
- duplicate sample IDs;
- insufficient sample count;
- wrong draw plan;
- unfrozen family;
- family member without a bundle;
- bundle not represented in the family;
- post hoc bundle creation.

Add a canonical validation command:

```bash
python3 -m certgen validate certificate-inputs \
  --study <frozen-study> \
  --family <family-id>
```

---

# 10. Phase F — Artifact-registry-driven next-action engine

Remove hardcoded late-stage paths from all current next-action logic.

The next-action engine must resolve artifacts from:

- artifact registry;
- study registry;
- family registry;
- merge manifest;
- reference draw-plan manifest;
- certificate-input manifest.

Do not hardcode paths such as:

```text
data/features/cvpr/features.npz
data/features/cvpr/sidecar.json
configs/cvpr/frozen_study.yaml
artifacts/cvpr/reference_draw_plan.json
```

Every next action must be generated from actual registered artifacts.

Required action fields:

```text
status
reason
exact_command
cwd
input_artifact_ids
input_paths
expected_output_artifact
success_validator
CPU_or_GPU
network_policy
planning_runtime
evidence_class
claim_permission
failure_recovery
```

Late-stage actions must be correct for:

```text
prepare reference draw
prepare controls
prepare certificate inputs
validate certificate inputs
run certificate
build partial ranking
run cross-feature analysis
stop and interpret
```

Add tests that create temporary artifact registries and verify exact commands.

---

# 11. Phase G — Family operational-completeness gate

A family must not be considered runnable merely because its metadata freezes.

Add a gate:

```bash
python3 -m certgen validate family-operational \
  --family <family-id> \
  --study <study>
```

It must verify:

- every family hypothesis exists;
- every hypothesis has one valid certificate-input bundle;
- all feature spaces are present;
- all control hypotheses are present;
- alpha allocation matches family size;
- no duplicate hypothesis IDs;
- no extra unregistered bundles;
- all preprocessing and extractor hashes match frozen declarations;
- all budgets are valid;
- all artifacts are claim-ineligible until real certificate execution.

Return:

```text
FAMILY_OPERATIONALLY_READY
```

only when all members are executable.

---

# 12. Phase H — Builder-faithful complete synthetic rehearsal

Create one end-to-end test that uses the actual canonical builders and registries.

Do not manually construct certificate NPZ files.

Required flow:

```text
fixture reference source
→ materialize fixture reference
→ select profile
→ freeze fixture study
→ prepare reference draw
→ prepare fixture preflight package
→ fake model and extractor preflight output
→ secure import
→ prepare generation package
→ fake generation output
→ secure import
→ prepare controls
→ prepare feature package
→ fake feature output
→ secure import
→ merge cache-v2
→ validate cache-v2
→ freeze family
→ prepare certificate inputs
→ validate family operational completeness
→ run synthetic certificates
→ build partial ranking
→ run cross-feature agreement
→ paper firewall denial
```

This must use:

- actual builder functions;
- actual CLI-compatible schemas;
- actual artifact registry;
- actual output schemas;
- actual secure importers;
- actual merge path;
- actual family builder;
- actual certificate-input builder.

Required negative tests:

- missing draw plan;
- overlapping null-control roles;
- missing corrupted control;
- missing feature role;
- wrong feature-space hash;
- stale worker version;
- missing family bundle;
- extra unregistered bundle;
- hardcoded missing path;
- mismatched study hash;
- changed alpha allocation.

---

# 13. Phase I — CLIP asset and redistribution policy

Create:

```text
docs/legal/CERTGEN_CLIP_ASSET_AND_REDISTRIBUTION_POLICY.md
```

The policy must distinguish:

```text
private research use
user-provided cache
private Kaggle dataset mount
public code release
public model-weight redistribution
```

Default policy:

```text
CLIP weights are not bundled in the public reproducibility archive.
The user supplies or privately mounts a validated cache.
The project records hashes, revision, and loader contract.
```

Do not claim redistribution rights that are not verified.

Add asset-manifest fields:

```text
redistribution_allowed
public_archive_included
user_provided
private_mount_required
license_source
license_status
```

The release builder must exclude CLIP weights unless explicit verified permission exists.

---

# 14. Phase J — Live-checkout versus portable-archive reporting

Separate all verification summaries into:

```text
LIVE_CHECKOUT_VERIFICATION
PORTABLE_ARCHIVE_VERIFICATION
```

The final report must not imply that the portable lane reproduces the complete live suite unless it actually does.

Required report fields:

## Live checkout

```text
test_count
integration_count
audit_count
notebook_count
mypy_critical
mypy_full_debt
paper_build
git_checks
```

## Portable archive

```text
member_count
archive_hash
portable_test_count
notebook_static_count
synthetic_rehearsal_status
git_dependent_tests_skipped_or_replaced
required_files
forbidden_metadata
```

Add a portable test manifest listing exactly which tests run and why.

---

# 15. Phase K — CVPR value upgrades

Implement only upgrades that directly improve the future paper and use outputs already planned.

## 15.1 Operational hypothesis coverage table

Generate:

```text
reports/CERTGEN_OPERATIONAL_HYPOTHESIS_COVERAGE.csv
```

Fields:

```text
family_id
hypothesis_id
comparison_type
feature_space
budget
input_bundle
bundle_valid
certificate_status
ranking_edge_status
paper_eligible
blocker
```

This makes missing family members impossible to hide.

## 15.2 Control validity dashboard artifact

Generate a machine-readable summary:

```text
controls_summary.json
```

Fields:

```text
null_control_status
obvious_gap_status
direction_status
preprocessing_status
reference_draw_status
family_operational_status
```

Do not create a web dashboard.

## 15.3 Certificate lineage card

For every certificate output, prepare a human-readable lineage card containing:

```text
study hash
family hash
comparison
feature space
reference draw
cache hashes
alpha
budget
decision
first crossing
censoring
limitations
```

## 15.4 Partial-ranking provenance

Every ranking edge must link to:

```text
certificate artifact
comparison ID
feature space
family ID
study hash
direct or transitive status
```

## 15.5 Cross-feature consensus policy

Define prospectively:

```text
direct agreement
direction disagreement
decided in one / unresolved in another
invalid in one
consensus edge eligibility
```

Do not force consensus when representations disagree.

## 15.6 Pilot stop/go report

Create a template that, after the 1k pilot, determines:

```text
STOP
REPAIR
SCALE_TO_10K
ADD_DINO
ADD_CFM
ADD_SECOND_BENCHMARK
```

Rules must be fixed before viewing outcomes.

---

# 16. Phase L — Canonical CLI additions

Add or finalize:

```bash
python3 -m certgen prepare reference-draw
python3 -m certgen prepare controls
python3 -m certgen prepare certificate-inputs
python3 -m certgen validate certificate-inputs
python3 -m certgen validate family-operational
python3 -m certgen readiness
python3 -m certgen next-action
```

Every command must support:

```text
--explain
--json
--dry-run where appropriate
```

Expected blockers must produce readable errors and nonzero exit codes without traceback-only output.

---

# 17. Phase M — Notebook and handbook updates

Regenerate the canonical notebooks only if required by new contracts.

Ensure:

- feature notebook includes control roles;
- feature outputs preserve draw-plan and control lineage;
- output schemas include worker contract version;
- resume validation uses the shared worker contract;
- copy-back instructions identify the next canonical command;
- no hardcoded late-stage paths appear.

Update the canonical execution handbook with the final exact sequence:

1. place official CIFAR archive;
2. validate reference;
3. materialize reference;
4. select pilot profile;
5. freeze study;
6. prepare reference draw;
7. prepare preflight package;
8. validate Kaggle input;
9. run real model/extractor preflight;
10. validate and import preflight output;
11. ingest runtime calibration;
12. prepare generation package;
13. validate generation input;
14. run 1k generation;
15. validate and import generation output;
16. prepare controls;
17. prepare feature package;
18. validate feature input;
19. run feature extraction;
20. validate and import feature output;
21. merge features;
22. validate cache-v2;
23. freeze family;
24. prepare certificate inputs;
25. validate family operational completeness;
26. run metric reproduction;
27. run sanity gates;
28. run certificates;
29. build partial ranking;
30. run cross-feature analysis;
31. generate pilot stop/go report;
32. stop and interpret.

For every step include:

```text
command
location
CPU_or_GPU
network_policy
input
output
runtime_class
resume
failure_recovery
evidence_class
claim_permission
completion_test
```

---

# 18. Phase N — Full verification matrix

Run:

```text
compileall
package imports
default non-recursive tests
integration audits
statistical lane
artifact-contract lane
runtime-hardening lane
real-execution-closure lane
final run-ready lane
worker-version tests
reference-draw tests
control-builder tests
certificate-input-builder tests
family-operational tests
artifact-registry next-action tests
complete builder-faithful synthetic rehearsal
cross-feature analysis tests
pilot stop/go tests
portable reporting tests
notebook static analyzer
deterministic notebook regeneration
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
portable archive build
portable archive verification
```

No test may:

- access the internet;
- require real CIFAR;
- require CUDA;
- load real models;
- create empirical paper evidence.

---

# 19. Final audit

Add:

```bash
python3 -m certgen audit final-pre-run --explain --json
```

It must independently verify:

- selected pilot profile valid;
- frozen study valid;
- reference draw builder exists and passes fixture execution;
- control builder exists and passes fixture execution;
- preflight package builder valid;
- generation package builder valid;
- feature package builder valid;
- worker contract consistent;
- output schemas consistent;
- cache-v2 merge valid;
- family builder valid;
- certificate-input builder valid;
- family operational-completeness gate valid;
- next-action paths artifact-driven;
- no hardcoded nonexistent paths;
- CLIP weights excluded from public archive;
- live and portable verification reported separately;
- full synthetic rehearsal passes;
- notebooks pass static checks;
- paper firewall remains closed;
- no `claim_allowed=true`;
- no local defect remains.

Possible status values:

```text
FINAL_PRE_RUN_AUDIT_FAILED
FINAL_PRE_RUN_LOCAL_DEFECT_REMAINS
CVPR_100_PERCENT_PRE_RUN_READY
```

Do not return the final status unless all checks pass.

---

# 20. Required final artifacts

Create:

```text
CERTGEN_CVPR_100_PERCENT_PRE_RUN_READINESS_REPORT.md
CERTGEN_CVPR_100_PERCENT_PRE_RUN_EXECUTION_HANDBOOK.md

reports/CERTGEN_FINAL_100_PERCENT_BASELINE.md
reports/CERTGEN_FINAL_100_PERCENT_COMMAND_LEDGER.csv
reports/CERTGEN_FINAL_100_PERCENT_CURRENT_STATE.json
reports/CERTGEN_FINAL_100_PERCENT_REPAIR_CHANGELOG.md
reports/CERTGEN_FINAL_100_PERCENT_TEST_MATRIX.md
reports/CERTGEN_FINAL_100_PERCENT_HANDOFF_AUDIT.md
reports/CERTGEN_FINAL_100_PERCENT_NOTEBOOK_READINESS.md
reports/CERTGEN_OPERATIONAL_HYPOTHESIS_COVERAGE.csv
reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv

docs/execution/CERTGEN_REFERENCE_DRAW_PLAN_PROTOCOL.md
docs/execution/CERTGEN_CONTROL_ARTIFACT_PROTOCOL.md
docs/execution/CERTGEN_CERTIFICATE_INPUT_BUNDLE_CONTRACT.md
docs/execution/CERTGEN_OPERATIONAL_FAMILY_GATE.md
docs/execution/CERTGEN_ARTIFACT_DRIVEN_NEXT_ACTION.md
docs/execution/CERTGEN_WORKER_VERSION_CONTRACT.md
docs/legal/CERTGEN_CLIP_ASSET_AND_REDISTRIBUTION_POLICY.md
docs/analysis/CERTGEN_PILOT_STOP_GO_PROTOCOL.md
docs/analysis/CERTGEN_CERTIFICATE_LINEAGE_CARD.md
docs/analysis/CERTGEN_PARTIAL_RANKING_PROVENANCE.md
```

Mark all prior execution handbooks as superseded.

---

# 21. Required final report structure

The final report must answer:

1. Is the complete local pipeline continuous?
2. Does the reference draw-plan builder work?
3. Do null and obvious-gap controls have executable artifact paths?
4. Does every family hypothesis have a certificate-input bundle?
5. Does the family-operational gate pass?
6. Are next actions generated from registered artifacts?
7. Are worker versions consistent?
8. Are resume markers fully validated?
9. Are live and portable verification reported separately?
10. Are CLIP weights excluded from the public archive?
11. Does the exact builder-faithful synthetic rehearsal pass?
12. Does any local pre-run defect remain?
13. What is the exact final status?
14. What is the exact next command?
15. Is any further pre-run patch justified?

The only acceptable stop-building conclusion, if earned:

> CertGen is 100% pre-run ready. No broad or targeted pre-run infrastructure development remains justified. All remaining work requires real reference input or real execution.

---

# 22. Final status taxonomy

Choose exactly one:

```text
FINAL_PRE_RUN_CLOSURE_FAILED
FINAL_PRE_RUN_CLOSURE_PARTIAL
FINAL_PRE_RUN_LOCAL_DEFECT_REMAINS
CVPR_100_PERCENT_PRE_RUN_READY
```

Expected, only if earned:

```text
CVPR_100_PERCENT_PRE_RUN_READY
```

Sub-status:

```text
BLOCKED_ONLY_BY_REAL_INPUTS_AND_REAL_EXECUTION
```

---

# 23. Exact next action

If the final audit passes, the singular next command must be:

```bash
python3 -m certgen validate reference \
  --source data/sources/cifar-10-python.tar.gz \
  --explain
```

Expected next status:

```text
READY_FOR_REFERENCE_MATERIALIZATION
```

Do not recommend another prompt or another build pass.

---

# 24. Completion condition

This task is complete only when:

1. baseline reproduced;
2. worker-version mismatch fixed;
3. reference draw-plan builder complete;
4. control builder complete;
5. certificate-input builder complete;
6. artifact-driven next-action engine complete;
7. family operational-completeness gate complete;
8. complete builder-faithful synthetic rehearsal passes;
9. CLIP redistribution policy enforced;
10. live and portable reporting separated;
11. operational hypothesis coverage generated;
12. certificate lineage and ranking provenance implemented;
13. pilot stop/go protocol frozen;
14. all local-safe tests and audits pass;
15. portable archive passes;
16. no local pre-run defect remains;
17. final status is `CVPR_100_PERCENT_PRE_RUN_READY`;
18. one exact next command is reported;
19. final report explicitly says no further pre-run patch is justified.

Begin by inspecting the live repository and reproducing the baseline.

Do not write the final verdict before the final audit runs.
