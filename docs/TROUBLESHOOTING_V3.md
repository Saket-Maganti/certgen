# Troubleshooting V3

`NO_REAL_EVIDENCE`

- Feature hash mismatch: regenerate sidecar or verify the feature file path.
- Vague preprocessing: replace `default`, `TBD`, or `unknown` with explicit resize/crop/interpolation/normalization.
- Claim gate failure: remove empirical interpretation and use non-claim diagnostic wording.
- Missing optional dependencies: use dry-run planning or install the extractor-specific optional stack outside tests.
