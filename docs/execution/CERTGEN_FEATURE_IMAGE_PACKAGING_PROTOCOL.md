# CertGen Feature Image Packaging Protocol

Feature inputs have two explicit modes:

- `EMBED_IMAGES_IN_PACKAGE` is mandatory by default for the 1k pilot. Images are copied to `images/reference/` and `images/<model_id>/`; all manifest paths are rewritten relative to the package root.
- `MOUNT_EXTERNAL_IMAGE_DATASET` is reserved for larger lanes and requires `mount_id`, `expected_mount_path`, and `mount_manifest_hash`.

`python3 -m certgen prepare features` consumes imported generation artifacts, the selected profile, reference manifest/draw plan, successful extractor preflight receipts, asset manifests, and observed preprocessing contracts. It writes the frozen config/profile, canonical role and image manifests, shards, extractor configs, assets, schemas, run identity, and deterministic ZIP.

The local builder opens, decodes, and hash-checks every embedded image. The feature notebook repeats this check before disk checks, GPU visibility, or worker allocation. Absolute Mac paths, traversal, missing images, decode failures, and hash mismatches block the run.
