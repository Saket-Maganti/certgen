# Actual extractor provenance audit

Result: **PASS**.

Feature extraction now writes `actual_runtime_provenance.json` from observed runtime sidecar values. It includes runtime extractor, model/processor classes, exact revision, preprocessing semantics/hash, layer, dimension, dtype, normalization, actual sample order/count, source manifest/payload, authenticated asset and inventory hashes, local-only status, dependency versions, device, and a self-hash. Resume requires the same validated file.

Scientific payload assembly reads that actual file, matches it to exactly one worker job and the NPZ bytes, and packages it verbatim; intended values are no longer synthesized as runtime facts. The payload validator verifies actual-versus-expected identity and exact aggregate extractor/role/shard coverage. Mutation and multipart/import tests reject wrong revision, processor, preprocessing, row order, source, missing/extra coverage, or self-hash. `claim_allowed=false`.
