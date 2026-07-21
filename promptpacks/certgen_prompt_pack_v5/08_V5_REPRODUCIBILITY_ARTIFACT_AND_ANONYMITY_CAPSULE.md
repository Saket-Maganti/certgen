# 08 — V5 Reproducibility Artifact and Anonymity Capsule

## Goal

Prepare the repository for an anonymous CVPR artifact/release capsule without leaking personal paths, secrets, or unsupported claims.

## Add Files

Create:

- `docs/reproducibility/REPRODUCIBILITY_CAPSULE_V5.md`
- `docs/reproducibility/ENVIRONMENT_V5.md`
- `docs/reproducibility/DATA_AND_SAMPLE_PROVENANCE_POLICY.md`
- `docs/reproducibility/FEATURE_CACHE_FORMAT.md`
- `docs/reproducibility/ZERO_COST_EXECUTION_GUIDE.md`
- `docs/release/ANONYMITY_AND_PRIVACY_AUDIT_V5.md`
- `certgen/audit/release_safety_v5.py`
- `tests/test_v5_release_safety.py`

## Reproducibility Capsule Must Include

- install instructions;
- CPU-only test instructions;
- optional Kaggle/Colab feature extraction instructions;
- expected commands;
- expected non-evidence smoke outputs;
- real-run command templates;
- feature-cache schema;
- provenance ledger schema;
- paper-build instructions;
- claim-gate explanation.

## Zero-Cost Requirements

State clearly:

- no paid APIs;
- no paid GPUs;
- no paid datasets;
- no paid annotation;
- released samples/features preferred;
- local/Kaggle/Colab free compute only.

## Release Safety Scan

Implement or extend a scanner for:

- absolute local paths like `/Users/saketmaganti/`;
- email addresses;
- API keys or tokens;
- personal names in release files unless intentionally in non-release metadata;
- fake result numbers;
- `claim_allowed=true` in non-evidence directories;
- files too large for release;
- cache files accidentally included.

## Anonymity Policy

Create a release profile:

- `release_profile=anonymous_cvpr`
- strip author identities from paper/release artifacts;
- allow project name CertGen;
- replace local paths with `<PROJECT_ROOT>`;
- ensure notebooks do not contain usernames.

## Tests

Tests should create small fixture files and verify:

- scanner catches local paths;
- scanner catches fake API keys;
- scanner catches claim leaks;
- scanner allows documented placeholders;
- release safety audit emits markdown + JSON.
