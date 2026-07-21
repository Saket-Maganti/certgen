# CertGen Kaggle dependency and asset guide

The Python 3.11 T4x2 profiles and locks are aligned under `requirements/`. The diagnostic uses the minimal `kaggle_t4x2_diagnostic` profile and `kaggle-diagnostic.lock`; it does not install the preflight stack. Generation, features, and preflight have separate locks and share `kaggle-constraints.txt`. The active CLIP route is Transformers-based, so neither `timm` nor `open-clip-torch` is required.

Supported dependency modes are `KAGGLE_INTERNET_ON_INSTALL`, `PRIVATE_WHEELHOUSE_OFFLINE`, and `USE_PREINSTALLED_VALIDATED`. Online mode installs only missing/incompatible requirements under the stage constraints. Offline mode recursively discovers any mount containing a valid `wheelhouse_manifest.json`, checks profile, Python/platform tags, distribution coverage, and every wheel hash, then installs with `--no-index`, `--find-links`, constraints, and the stage lock. Preinstalled mode installs nothing and fails if any version/import is incompatible.

After installation and any required kernel restart, each notebook reruns version inspection, actual imports, and `python -m pip check`. It writes `dependency_report.json`, `dependency_freeze.txt`, `pip_check.txt`, `import_smoke_test.json`, and `kernel_restart_required.json` when applicable.

Private asset datasets may use any Kaggle dataset slug, mount name, and safe nesting. CertGen discovers `asset_manifest.json`, then matches asset ID, model/extractor ID, revision, license status, loader type, inventory hash, and file hashes. Runtime mount paths are recorded in run logs and never written into frozen scientific configuration. Multiple unrelated model datasets are safe when one manifest matches; multiple exact matches fail explicitly.

The minimum CIFAR pilot uses Inception and the Transformers CLIP loader. Public archives contain no model/extractor weights; CLIP remains private and `local_files_only=True`. `claim_allowed=false`.
