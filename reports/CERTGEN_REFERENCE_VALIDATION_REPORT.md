# CIFAR-10 reference validation

Status: `PASS`.

- Canonical source: `data/sources/cifar-10-python.tar.gz`
- Size: `170498071` bytes
- SHA-256: `6d958be074577803d12ecdefd02955f39262c83c16fe9348329d7fe0b5c001ce`
- Contract: official CIFAR-10 Python tarball hash, safe members, required batches, decoded 32×32 RGB images, labels, and counts passed.
- Materialization: `10000` deterministic test-split reference rows at `registry/manifests/cvpr/cifar10_reference.jsonl`.
- Raw archive and materialized images remain ignored and untracked.

The Kaggle competition test archive was not substituted. `claim_allowed=false`.
