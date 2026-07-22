# CertGen Expected identity binding

Status: `PASS`

The versioned `certgen.expected_package_identity.v1` contract binds package SHA-256, scientific identity, configuration, run, optional study/profile/scale, source inventory hash, integrity manifest, package type/stage, and output schema. Diagnostic and preflight notebooks embed their active identity; generation/feature notebooks without a built active bundle and all generic notebooks require an explicit identity and reject same-stage defaults.

No real Kaggle execution or empirical evidence is represented. `claim_allowed=false`.
