# 12 — V4 Reproducibility Capsule and Release Safety

Build release-readiness infrastructure early.

## Goal

CertGen should be recipe-first and zero-cost. V4 should create a reproducibility capsule validator and release safety checks so the project can eventually ship with confidence.

## Implement

Create:

- `certgen/release/capsule.py`
- `certgen/release/privacy_scan.py`
- `certgen/release/license_scan.py`
- `certgen/cli/validate_repro_capsule.py`
- `certgen/cli/run_release_safety_scan.py`
- `docs/REPRODUCIBILITY_CAPSULE_V4.md`
- `docs/RELEASE_SAFETY_V4.md`
- `release/README.md`
- tests.

## Capsule requirements

A reproducibility capsule should include:

- command index,
- environment info,
- dependency list,
- data/source registry templates,
- feature-cache schema,
- preprocessing locks,
- run plans,
- certificate configs,
- report generation commands,
- evidence status policy,
- limitations/no-results notes.

The capsule should not include:

- private paths,
- secrets,
- paid tokens,
- copyrighted sample images unless license permits,
- large feature caches by default,
- fake results.

## Safety scan

Scan release docs and generated artifacts for:

- absolute local paths like `/Users/...`,
- API keys/secrets patterns,
- unguarded fake result claims,
- `claim_allowed=true` in smoke/synthetic folders,
- FID rigorous certificate language,
- missing license fields,
- oversized files if a threshold is configured.

## Output

- `docs/V4_RELEASE_SAFETY_REPORT.md`
- `data/results/v4_release_safety.json`
- `release/CAPSULE_MANIFEST.json`

## Acceptance criteria

- Capsule validator passes on template-only capsule.
- Release scan catches intentionally bad temporary fixtures.
- No private local path is present in release-facing files, unless explicitly allowed in ignored run logs.
- Tests remain local and fast.
