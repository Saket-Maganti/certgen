# Kaggle asset setup

Status: `PLANNING_ONLY_NOT_EMPIRICAL_EVIDENCE` · `claim_allowed=false`

The public CertGen input ZIPs contain no model or extractor weights. Create a private Kaggle Dataset under any owner, slug, or display name and attach it anywhere under an approved search root. Filenames and mount names are not identity. One valid example is:

```text
/kaggle/input/certgen-private-assets/
  asset_manifest.json
  google-ddpm.asset.json
  frank-ddpm.asset.json
  inception.asset.json
  clip.asset.json
  google_ddpm_cifar10_candidate/
  frank_ddpm_ema_cifar10_candidate/
  inception/
  clip-vit-large-patch14/
```

The aggregate `asset_manifest.json` v2 must record each relative file, byte size, SHA-256, asset ID, model/extractor ID, exact provider revision, snapshot root, per-asset manifest path, supported loader type, and approved license status. Each per-asset manifest binds the complete local snapshot inventory and `local_files_only=True` loader contract. Missing, extra, unhashed, stale-revision, escaped, conflicting, or symlinked files stop the notebook before model loading. The shown directory names are illustrative and may be changed; workers use only the validated runtime resolution map and never guess `mount_subdir` paths.

CLIP weights are specifically excluded from every public archive. They require this private mount (or an equivalent user-provided validated cache) and must be loaded with `local_files_only=True`.

Dependency installation is independent of model-asset access. Select exactly one mode:

- `KAGGLE_INTERNET_ON_INSTALL`: Kaggle Internet on only while installing the pinned lock; model loaders remain offline.
- `PRIVATE_WHEELHOUSE_OFFLINE`: Kaggle Internet off and a private wheelhouse at any searched mount/location with a valid `wheelhouse_manifest.json`.
- `USE_PREINSTALLED_VALIDATED`: no installation; every installed version must already satisfy the stage lock.

After dependencies validate, turn Kaggle Internet off for all model loading and execution. If installation requests a restart, restart and rerun the same cell; the input-bound marker is automatic. The notebook writes `dependency_report.json`, `dependency_freeze.txt`, `pip_check.txt`, `import_smoke_test.json`, `wheelhouse_validation_report.json` when applicable, and `asset_resolution_report.json` before any expensive operation.
