# Model Asset Policy

Each frozen run selects exactly one policy:

- `ONLINE_PREFLIGHT_DOWNLOAD`: internet must be enabled only for checkpoint preflight. The worker resolves the pinned revision into an explicit local cache, inventories expected files, sizes and SHA-256 hashes, and emits a portable asset manifest. Generation/features then run local-only.
- `OFFLINE_PACKAGED_CACHE`: internet must be disabled. The uploaded cache must already contain every expected config, tokenizer, scheduler, processor and weight file. Membership, revision, size and hashes are checked before model load.

Unknown or manual-review licenses block preparation. A registry label is not approval. Cache and asset manifests are `run_log_only`, `claim_allowed=false`; missing assets, revision mismatch, hash mismatch, unexpected network state, or token-policy mismatch fail before GPU work.
