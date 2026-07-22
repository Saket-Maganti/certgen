# CertGen Asset resolution

Status: `PASS`

Aggregate manifests are found recursively and validated for exact file hashes, revision, loader, license, snapshot containment, per-asset manifest hash, and duplicate content. The runtime-only report passes concrete existing snapshot roots into workers; offline workers revalidate the per-asset manifest and never create or guess an empty cache. Loaders use `local_files_only=True`.

No real Kaggle execution or empirical evidence is represented. `claim_allowed=false`.
