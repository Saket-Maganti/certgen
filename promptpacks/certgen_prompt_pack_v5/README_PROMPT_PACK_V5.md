# CertGen Prompt Pack V5

**Pack name:** CertGen Prompt Pack V5 — CVPR-Ready-Except-Runs Upgrade  
**Target project:** `/Users/saketmaganti/Projects/certGen`  
**Target venue:** CVPR 2027 Main Conference  
**Pack purpose:** Bring CertGen as close as possible to a CVPR-ready paper/release state **without fabricating, simulating, or promoting real empirical evidence**.

---

## What V5 Is

V5 is a **paper-readiness and execution-readiness pack**. It should convert the V4 real-pilot-ready system into a complete CVPR-facing research machine with:

- locked paper identity;
- real-citation related-work board;
- analysis-plan/preregistration lock;
- result contracts;
- figure/table builders with placeholders and schema checks;
- CVPR paper scaffold;
- supplement scaffold;
- proof appendix scaffold;
- ethics/limitations/reproducibility sections;
- reviewer-attack harness;
- author-response bank;
- artifact release capsule;
- anonymity/privacy/release scans;
- final CVPR-ready-except-runs audit.

V5 should **not** claim real results. It should prepare every slot where results will later be injected.

---

## Current Known Starting State

The user reports that V4 has been implemented and verified:

- V4 final audit passed 27/27.
- Tests passed: 92 passed.
- `claim_allowed=false`.
- `evidence_status=dry_run_only`.
- No fake real evidence.
- No real benchmark audit.
- No decidedness fraction claim.
- No ranking movement claim.
- No rigorous FID claim.

V4 added:

- real-run planner;
- notebook generator;
- preprocessing locks;
- batch certificates;
- multiple-comparison/dependence diagnostics;
- decidedness/ranking reports;
- first-real-pilot controller;
- literature claim tracing;
- paper artifact scaffolds;
- reviewer attack harness;
- reproducibility capsule;
- release safety scan.

V5 must begin by verifying this state from files and tests. Do not trust the summary blindly.

---

## How to Use This Pack

Use the files in order:

1. `00_V5_GLOBAL_RULES_AND_STOP_CONDITION.md`
2. `01_V5_STATE_INTAKE_AND_GAP_AUDIT.md`
3. `02_V5_CVPR_PAPER_IDENTITY_AND_CLAIM_CONTRACT.md`
4. `03_V5_REAL_CITATION_RELATED_WORK_BOARD.md`
5. `04_V5_PREREGISTRATION_AND_ANALYSIS_PLAN_LOCK.md`
6. `05_V5_RESULT_CONTRACTS_TABLES_AND_FIGURE_MANIFESTS.md`
7. `06_V5_PAPER_SCAFFOLD_MAIN_TEX.md`
8. `07_V5_SUPPLEMENT_PROOF_AND_STATISTICAL_APPENDIX.md`
9. `08_V5_REPRODUCIBILITY_ARTIFACT_AND_ANONYMITY_CAPSULE.md`
10. `09_V5_EXECUTION_RUNBOOKS_AND_COMMAND_BUNDLES.md`
11. `10_V5_RESULT_INJECTION_AND_CLAIM_TRACE_SYSTEM.md`
12. `11_V5_REVIEWER_SIMULATOR_AND_AUTHOR_RESPONSE_BANK.md`
13. `12_V5_CVPR_READINESS_SCORECARD_AND_KILL_LIST.md`
14. `13_V5_FINAL_AUDIT_AND_HANDOFF.md`

The one-shot prompt exists only for emergency use. Prefer staged execution.

---

## V5 Success Definition

V5 succeeds if, after implementation:

- all tests pass;
- V5 final audit passes;
- paper scaffold builds or at least validates structurally;
- supplement scaffold exists;
- related-work board uses real citation placeholders/tasks, not fake citations;
- no result number is promoted without evidence;
- every table/figure has a schema and result-injection contract;
- every claim is traceable to an artifact or blocked;
- release capsule and anonymity/privacy scans pass;
- the project handoff says clearly: **next step is real execution, not more infrastructure**.

---

## V5 Non-Goal

V5 is not the real experiment. Do not download large datasets, run heavy GPU jobs, generate samples, or claim any real undecided fraction unless the user explicitly runs the real pilot and provides verified outputs.

---

## Final Rule

After V5, do not build V6 generic infrastructure unless real execution exposes a concrete bug, missing gate, schema mismatch, proof issue, paper-build failure, or release-safety issue.

The next real action after V5 should be:

> populate one real provenance ledger, validate/materialize real feature caches, reproduce one reported point estimate, and run the first real clean-core pilot in non-claim mode.
