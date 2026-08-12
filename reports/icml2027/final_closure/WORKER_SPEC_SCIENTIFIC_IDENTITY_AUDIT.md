# Worker-spec scientific-identity audit

Every executable worker spec requires schema/lane, study ID/hash, configuration SHA-256, authenticated prerequisite-set SHA-256, applicable reference plan, model and extractor revisions, preprocessing hashes, seed-plan and sample-policy hashes, expected prefix hashes/counts/shards/coverage, output schema, and `claim_allowed=false`.

Generation partitions prove exact union, empty intersections, both frozen models, and exact seed-record hashes. Feature partitions prove every extractor × source-role × shard occurs exactly once with the same source order. Gap, overlap, wrong model/extractor, duplicate shard, extra shard, and hash mutations fail closed.

The two-pass builder first computes the authenticated prerequisite-set hash, then creates a worker spec with `scripts/icml2027/build_worker_spec.py`, then builds the final ZIP. Authentic bytes for the wrong experiment are rejected.
