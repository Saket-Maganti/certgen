# CertGen Output Schema and Import Contract

`certgen/cvpr/output_schemas.py` is the sole owner of preflight, generation, and feature output schema versions, complete status codes, required roots, allowed roots, and member safety. Notebook root statuses embed the same version; the static analyzer, dry validator, and importer consume it.

Supported roots include identity, status, orchestration, per-asset/model/extractor/shard output, caches, manifests, logs, smoke images, images, features, sidecars, merge index, integrity manifest, and recovery instructions. Traversal, absolute paths, case-colliding duplicates, symlinks, executables, nested archives, oversized expansion, unsupported roots, integrity mismatches, incomplete workers, and `claim_allowed=true` are rejected before extraction.
