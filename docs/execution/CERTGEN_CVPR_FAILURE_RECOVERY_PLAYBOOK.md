# CertGen CVPR Failure Recovery

Preserve raw ZIP/logs/config hashes. Dependency or checkpoint failure -> fix only the preflight package and rerun failed models. Partial generation/feature shard -> quarantine the invalid shard and rerun the exact deterministic assignment. Hash/schema/preprocessing/reference mismatch -> stop; local repair is allowed only for derived metadata that can be regenerated without changing raw bytes. Provenance, metric reproduction, null, direction, family, or paper firewall failure -> no scale-up or claim promotion.
