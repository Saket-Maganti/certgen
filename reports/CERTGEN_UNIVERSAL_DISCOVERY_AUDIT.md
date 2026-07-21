# CertGen universal discovery audit

Status: `UNIVERSAL_DISCOVERY_PASS`

The canonical scanner is recursive, bounded to depth/candidate/member/byte limits, does not follow symlinks, rejects unsafe/case-colliding/nested archive members, verifies integrity manifests, and selects by structured package identity. ZIP and already-extracted forms are supported.

Account-specific runtime path findings: `0`.

Runtime locations are excluded from scientific identity hashes. `claim_allowed=false`.
