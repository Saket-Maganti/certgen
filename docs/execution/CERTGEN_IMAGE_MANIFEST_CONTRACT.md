# CertGen Image Manifest Contract

`schemas/cvpr/image_manifest.schema.json` and `certgen.cvpr.image_manifest` define the only schema emitted by new generation and feature code.

Every row contains: `sample_id`, `role`, `model_id`, `relative_image_path`, `image_hash`, `seed`, `prompt_or_class_id`, `width`, `height`, `mode`, `source_run_id`, and `source_manifest_hash`.

Validation requires unique sample IDs and paths, safe relative POSIX paths, no traversal, a valid role/model identity, lowercase SHA-256 hashes, positive dimensions, a supported decoded mode, complete lineage, file existence, matching image bytes, and matching decoded dimensions/mode. New emitters reject legacy `path`, `image_path`, and `source_path` fields. A separate explicit migration helper exists only for historical imports.

The schema is shared by generation batches, generation manifests, feature preparation, feature shards, workers, merge lineage, and cache-v2 sidecars.
