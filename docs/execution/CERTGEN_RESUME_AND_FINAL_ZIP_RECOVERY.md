# CertGen Resume and Final ZIP Recovery

A reusable worker marker requires `status=success`, the expected schema and worker version, matching configuration/input/asset hashes, and existing output files with matching SHA-256 values. Invalid markers are quarantined and rerun; marker existence alone is never sufficient.

Final ZIP behavior is idempotent. Resume reuses a ZIP only when its recorded hash, identity, members, sizes, and content hashes match the completed run. Missing or corrupt ZIPs are rebuilt without rerunning valid shards. Restart quarantines the prior ZIP. Force-new-run requires a new run-specific path. A rebuild is validated before its status is written.
