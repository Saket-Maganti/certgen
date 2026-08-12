# ICML notebook bootstrap audit

All nine deterministic ICML notebooks begin with an embedded stdlib-only
archive discovery/authentication cell. The cell binds an explicit expected ZIP
SHA-256 and lane, rejects traversal/symlink/collision/resource violations,
verifies exact membership plus every inventory hash, atomically extracts, and
only then adds authenticated `source/` to `sys.path`. Static tests reject any
pre-auth `import certgen` or `from certgen`. `claim_allowed=false`.
