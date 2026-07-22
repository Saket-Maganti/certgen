# CertGen Pre-import authentication

Status: `PASS`

The notebook executes one SHA-256-frozen stdlib-only bootstrap. It bounds recursive discovery; rejects unsafe ZIP/directory forms; verifies exact membership, every size/hash, the complete Python source inventory, and the exact expected identity; atomically materializes; and only then adds the authenticated root to `sys.path`. Focused regressions cover modified/absent code, extra files, wrong hashes/identity, traversal, case collisions, special entries, and extracted symlinks.

No real Kaggle execution or empirical evidence is represented. `claim_allowed=false`.
