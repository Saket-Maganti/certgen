# Scientific payload contract

Generation and feature READY lanes no longer close with metadata-only ZIPs. Preflight-only lanes may.

Generation uses `<lane>.output.index.json` plus ordered `.partNNN.zip` files containing PNG shards, per-shard JSONL manifests, frozen sample IDs and generator seeds, checkpoint revisions, image hashes, runtime results, dependency verification, worker spec, and scientific identity.

Features use the same multipart index with NPZ shards and exact sidecars. Validation checks sample order, count, dimension, dtype, finiteness, extractor revision, preprocessing hash, source-manifest identity, shard integrity, runtime, and provenance.

The index binds study/configuration, ordered part name/hash/size, global payload-manifest hash, sample coverage, and `claim_allowed=false`. Missing parts, corrupt bytes, unsafe paths, symlinks, duplicates, wrong membership, row-order drift, and identity mutations fail closed. `payload_index_sha256` authenticates the complete index without an impossible self-referential identity field.

CLI: `python3 -m certgen icml2027 payload validate <index> [--type generation|features] [--seed-manifest ...] [--worker-spec ...]`. Copy-forward receipts preserve the source index and ordered part identities; local import revalidates before extraction.
