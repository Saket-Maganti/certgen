# Worker Version Contract

All orchestrators and workers use `certgen.notebooks.worker_contract`. Current completion markers bind worker-contract version, worker type, implementation version, configuration schema, and output schema. Resume accepts an exact current identity or a narrowly enumerated compatible legacy identity; missing, stale, mixed, or incompatible markers are rejected. Completion compatibility never relaxes configuration, input, asset, or output hashes.
