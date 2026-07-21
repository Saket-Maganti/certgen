# Clean Archive Guide

Create the canonical export only after final local checks:

```bash
python3 -m certgen release build-archive --out dist/certgen_cvpr_reproducibility.zip
```

The builder preserves canonical paths, including `notebooks/kaggle/`; includes source, tests, configs, canonical docs, paper source, release manifests and required root/report files; and excludes Git metadata, macOS metadata, bytecode/tool caches, generated paper products, local datasets, ADE20K, raw caches, temporary notebooks and quarantine.

It refuses overwrite, writes deterministic timestamps/modes, adds per-member hashes, extracts to a temporary non-Git directory, checks imports and required paths, runs the portable test lane, scans user-facing text for private absolute paths, and writes an archive SHA-256 plus adjacent manifest. The archive and manifest remain `release_validation_only`, `claim_allowed=false`.
