# CertGen dependency closure report

Status: `DEPENDENCY_CLOSURE_PASS`

The diagnostic profile is minimal and uses `kaggle-diagnostic.lock`. Generation, features, and preflight profiles resolve transitively through their stage locks and shared constraints. The active CLIP route uses Transformers; `timm` and `open-clip-torch` are not required.

Online install, manifest-verified private-wheelhouse install, preinstalled validation, kernel-restart, import-smoke, missing-wheel, and `pip check` failure paths are fixture-tested. `claim_allowed=false`.
