# CertGen Transactional Replacement Audit

Status: `REPLACEMENT_VERIFIED`

- Expected and observed ZIP SHA-256: `d1a144dfa317f766b4c86e108a605de9a346e5e0cbb071b2f29d70e17bf530af`.
- Archive inspection: 1,239 members under one `certGen/` root; no traversal, absolute paths, symlinks, malformed entries, or nested archives.
- Git preserved: branch `master`, HEAD `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`.
- User-owned runtime inputs preserved: none were present. No `.env` file or real source/reference/generated/feature artifact was found.
- Old source merged into replacement: `false`.
- Replacement verification: compile/import pass; focused post-cache lane `9 passed`; portable archive verified; five notebooks static-pass; final pre-run audit `24/24` with `CVPR_100_PERCENT_PRE_RUN_READY`.
- Transaction staging and rollback directories were deleted after verification.

This audit is repository-integrity evidence only. It is not empirical model evidence. Claim allowed: `false`.
