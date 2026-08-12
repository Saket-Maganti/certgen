# ICML dependency lifecycle audit

Result: PASS in CPU fixtures. READY notebooks authenticate with stdlib first, import only authenticated source, select an exact lane lock, validate installed distributions, install only under an allowed mode, run `pip check` and import smoke, write a report/marker, require restart after installation, and verify the same identity on the second pass.

Marker fields: lane, input ZIP SHA-256, source-tree SHA-256, dependency-profile ID, dependency-lock SHA-256, Python version, platform, and `claim_allowed=false`. Stale source/package/lock/lane markers fail closed.

- Compatible environment: `True`
- Offline exact-lock install requested restart: `True`
- Identity-bound second pass: `True`
- Tested modes: `USE_PREINSTALLED_VALIDATED`, `KAGGLE_INTERNET_ON_INSTALL` planning branch, and `PRIVATE_WHEELHOUSE_OFFLINE` fixture.
- Negative tests: incompatible preinstalled environment, stale marker, wrong identity, missing wheel coverage, `pip check`/verification failure, and import-smoke propagation.

The fixture does not assert the contents of a future Kaggle base image. Each real launch still validates or installs its authenticated exact lock. `claim_allowed=false`.
