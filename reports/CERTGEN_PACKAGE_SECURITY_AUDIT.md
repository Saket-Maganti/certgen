# CertGen package security audit

Status: `PACKAGE_SECURITY_TESTS_PASS`

Covered controls: traversal, absolute/backslash paths, symlinks and special links, case-folded duplicates, nested archives, expansion/member/candidate/depth limits, extracted-package extra files, exact hashes, safe YAML, no code execution during classification, and explicit ambiguity failure.

The audit uses synthetic fixtures only. `claim_allowed=false`.
