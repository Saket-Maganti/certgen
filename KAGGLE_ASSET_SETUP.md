# Kaggle asset setup

Status: `PLANNING_ONLY_NOT_EMPIRICAL_EVIDENCE` · `claim_allowed=false`

The public CertGen input ZIPs contain no model or extractor weights. Create a private Kaggle Dataset named `certgen-private-assets`, attach it to the notebook, and preserve this mount layout:

```text
/kaggle/input/certgen-private-assets/
  asset_manifest.json
  google_ddpm_cifar10_candidate/
  frank_ddpm_ema_cifar10_candidate/
  inception/
  clip-vit-large-patch14/
```

`asset_manifest.json` must record each relative file, byte size, SHA-256, asset ID, provider revision, and license-review status. The immutable configuration and manifest hashes must match the uploaded input bundle. Missing, extra, unhashed, stale-revision, or symlinked files stop the notebook before model loading.

CLIP weights are specifically excluded from every public archive. They require this private mount (or an equivalent user-provided validated cache) and must be loaded with `local_files_only=True`.

Dependency installation is independent of model-asset access. Select exactly one mode:

- `KAGGLE_INTERNET_ON_INSTALL`: Kaggle Internet on only while installing the pinned lock; model loaders remain offline.
- `PRIVATE_WHEELHOUSE_OFFLINE`: Kaggle Internet off and a private wheelhouse mounted at `/kaggle/input/certgen-wheelhouse`.
- `USE_PREINSTALLED_VALIDATED`: no installation; every installed version must already satisfy the stage lock.

After dependencies validate, turn Kaggle Internet off for all model loading and execution. The notebook writes `dependency_report.json`, `dependency_freeze.txt`, `pip_check.txt`, and an asset-validation report before any expensive operation.
