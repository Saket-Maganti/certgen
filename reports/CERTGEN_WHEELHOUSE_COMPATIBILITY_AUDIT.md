# CertGen Wheelhouse compatibility

Status: `PASS`

Exact v2 wheelhouses validate manifest membership, size/hash, distribution, locked version/specifier, and tags against CPython 3.11 on Linux x86_64. manylinux x86_64 and `py3-none-any` are accepted; macOS/ARM, wrong Python/ABI, sdists, wrong versions, corrupt or unmanifested files, and conflicting copies are rejected.

No real Kaggle execution or empirical evidence is represented. `claim_allowed=false`.
