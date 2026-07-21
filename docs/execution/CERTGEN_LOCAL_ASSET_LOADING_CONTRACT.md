# CertGen Local Asset Loading Contract

Every asset manifest records `asset_root`, `snapshot_path`, `source_repo`, `revision`, files, hashes, total size, `layout_type`, and `loader_type`. The snapshot must be contained by the asset root and all declared file hashes must validate before GPU load.

Direct snapshots are loaded as `from_pretrained(snapshot_path, local_files_only=True)`. A remote repository ID is never combined with a direct snapshot root as `cache_dir`. Hugging Face cache layout, Torchvision weight enums, and package resources have distinct loader types. Generation and feature workers refuse online model-asset access.
