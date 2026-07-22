# CertGen final dependency closure

Status: `PASS`

All four Kaggle Python 3.11 profiles have their active imports and profile requirements in the stage locks; every locked name is pinned by the shared constraints file. The Transformers CLIP route is retained and `timm`/`open-clip-torch` remain absent. Online-install, exact offline-wheelhouse, and validated-preinstalled modes are covered, including restart-marker consumption, import smoke, and `python -m pip check`.

This is dependency-contract evidence only; it is not empirical evidence and `claim_allowed=false`.
