# Authenticated generator asset-loading audit

Result: **PASS in CPU/mock execution; real private assets remain external**.

The confirmatory `run_generation_samples` path requires an authenticated snapshot root and exact asset identity. Runtime discovery validates the aggregate and per-asset manifests, revision, inventory, loader type, symlink containment, and optional local weight file. `DDPMPipeline.from_pretrained` receives only the resolved local snapshot plus `local_files_only=True`; it receives no remote model ID.

The legacy convenience generator remains available outside the prospective confirmatory route. The 10k worker never calls it. A fake Diffusers rehearsal asserted the exact local call and deterministic PNG output. Wrong scientific worker fields, asset identities, and seed partitions fail closed in the broader execution suite. `claim_allowed=false`.
