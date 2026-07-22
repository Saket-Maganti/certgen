# CertGen release verification

Status: `PASS`

- Candidate archive: `dist/certgen_final_kaggle_execution_path_release_final.zip`
- Size: `2628049` bytes
- Members: `899`
- SHA-256: `80e0a3858ae272bb789972f7772f2db11aad0bf337e48aaf35bd165f2c82c272`
- Fresh-extraction import: `PASS`
- Portable focused tests: `36 passed`
- Fresh-extraction compileall, import, deterministic notebook regeneration, privacy, secret, and release scans: `PASS`
- Notebook static validation: `PASS`
- Builder-faithful synthetic closure: `PASS` with all 27 stages
- Private-path, restricted-asset, unsafe-member, and excluded-cache checks: `PASS`
- Diagnostic and preflight bundle manifest verification: `PASS`

The archive excludes Git metadata, raw/materialized CIFAR data, weights, private assets and wheelhouses, generated images, feature caches, returned Kaggle outputs, credentials, temporary logs, caches, and quarantine payloads. It contains the authenticated diagnostic/preflight bundles, canonical notebooks, exact execution-path tests, dependency locks, and final contract reports.

This is release-validation evidence only, not empirical evidence. `claim_allowed=false`.
