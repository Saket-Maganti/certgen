# CertGen Kaggle dependency and asset guide

The stage locks under `requirements/` pin the Python 3.11 T4x2 environment and share `kaggle-constraints.txt`. Supported modes are `KAGGLE_INTERNET_ON_INSTALL`, `PRIVATE_WHEELHOUSE_OFFLINE`, and `USE_PREINSTALLED_VALIDATED`. Each notebook runs `python -m pip check` and writes `dependency_report.json`, `dependency_freeze.txt`, and `pip_check.txt`.

The minimum CIFAR pilot uses Inception and the Transformers CLIP loader; DINO and CFM are not forced. Public archives contain no weights. CLIP always requires a private validated mount or equivalent user cache. See `KAGGLE_ASSET_SETUP.md` for the exact mount layout and fail-closed manifest contract. `claim_allowed=false`.
