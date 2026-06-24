# Prompt 00 — Global Rules for All CertGen V1 Work

You are implementing **CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison**.

Before doing any work, read `CERTGEN_PROJECT_MASTER_CONTEXT.md` completely. Treat it as the source of truth.

## Core idea

CertGen is a zero-cost, reproducible, statistically disciplined tool that wraps generative-evaluation metrics in a decision/certificate layer. The goal is to decide **when one generative model is certifiably better than another**, how many samples were needed, and whether reported wins in the literature are actually statistically decided.

CertGen is **not**:

- a new metric paper;
- a “FID is bad” paper;
- a leaderboard replacement;
- a dataset paper;
- a claim that published papers are wrong;
- a new statistical theory paper.

CertGen is:

- a metric-agnostic decision/certificate layer;
- an optional-stopping-safe comparison protocol;
- a samples-to-decision tool;
- eventually, a literature audit of decided vs. undecided generative-model wins.

## Hard constraints

Do not use or require:

- paid APIs;
- paid GPUs;
- paid datasets;
- paid annotation;
- hosted inference;
- automatic large downloads in tests;
- mandatory heavy dependencies;
- GPU in unit tests.

Allowed:

- local CPU tests;
- free Kaggle/Colab for later feature extraction;
- public/free datasets;
- released generated samples/features/checkpoints;
- optional lazy imports for heavy feature extractors.

## Statistical guardrails

1. **Clean core metrics:** KID/MMD/CMMD-style metrics are the clean target for rigorous certificates because they can be expressed through estimators with per-unit or batched contribution streams.
2. **FID landmine:** FID is a nonlinear biased functional of empirical means and covariances. Do not claim a rigorous anytime-valid FID certificate by simply treating FID as a sample mean.
3. **FID allowed status in V1:** FID may be implemented descriptively and may have a clearly marked block/batch exploratory path. Any artifact using FID must label the certificate status as `descriptive_only`, `approximate`, or `not_rigorous` unless a later proof makes it watertight.
4. **Optional stopping demonstration:** V1 should prepare for, but not necessarily fully execute, the demonstration that naive peeking inflates false-decision rate while the certificate controls it.

## Evidence rules

Every artifact must have an evidence status:

- `real_evidence_candidate`
- `non_evidence_smoke`
- `non_evidence_mock`
- `non_evidence_synthetic`
- `non_evidence_planned`
- `descriptive_only`

V1 should only produce non-evidence artifacts.

No result can be called:

- certified;
- paper evidence;
- empirical result;
- literature audit finding;
- model win;
- ranking change;
- compute saving;

unless the relevant real-data gates pass in a later version.

## Coding style

- Keep code modular and boring.
- Prefer standard library + numpy/pandas/scipy/sklearn/pytest where useful.
- Heavy vision/model libraries must be optional and lazy.
- Every command should have `--dry-run` where practical.
- Every output file should include provenance: config hash, code version placeholder, command, timestamp, evidence status, input manifest paths.
- Tests must run quickly on CPU.

## Completion format

At the end of each prompt, report:

1. files created/modified;
2. commands added;
3. tests added;
4. tests run and results;
5. known limitations;
6. next prompt to run.

Do not fabricate passing tests. If tests are not run, say so explicitly.
