# CertGen Feature Package and Merge Contract

Feature preparation consumes canonical generation and preflight imports, a materialized reference, frozen draw plan, extractor preflight, observed preprocessing, asset manifests, and image hashes. It writes a deterministic role manifest, non-mixing stable-ID shards, extractor configs, preprocessing contracts, expected output schema, identity, and instructions.

After secure import, run `python3 -m certgen merge features --run <run_id>`. The merge validates shard schema, hashes, extractor identity, preprocessing hash, dimensions, finite values, and unique sample IDs; sorts by sample ID; preserves role/model grouping; writes atomic arrays and cache-v2 sidecars; validates every cache; writes `merge_manifest.json` and `status.json`; and registers artifacts. Failed partial output is quarantined and never reused.
