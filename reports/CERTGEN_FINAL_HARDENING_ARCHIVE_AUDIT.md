# Final Hardening Archive Audit

Status: `ARCHIVE_VERIFIED`.

Command: `python3 -m certgen release build-archive --out dist/certgen_cvpr_reproducibility.zip`
Exit: `0`
Archive: `dist/certgen_cvpr_reproducibility.zip`
Manifest: `dist/certgen_cvpr_reproducibility.zip.manifest.json`
SHA-256: `9c6892c5fcf3cb8a9ba8a2f39b4601744ae66ef1eeebc98d40df1bbf5dc00521`
Size: approximately 796 KiB
Members: `688` including the internal manifest
Temporary extraction/import: pass, exit `0`
Portable non-Git test: `1 passed in 0.06s`
Canonical notebook paths: `5/5` present under `notebooks/kaggle/`
Forbidden metadata/dataset/quarantine members: `0`
User-facing private absolute paths: `0`
ADE20K roots/data: excluded
Evidence class: `release_validation_only`; claim permission: `false`.

The adjacent machine manifest contains every member path, size and SHA-256. This audit is intentionally external to the ZIP so it can report the ZIP's final hash without a self-referential archive hash.
