# DINOv2 GO/NO-GO

Engineering status: `READY_AFTER_AUTHENTICATED_ASSET_AND_LICENSE_REVIEW`. The local model+processor adapter, canonical worker, actual provenance, robustness-only payload, and offline fixture pass.

Real-run recommendation: **`NO_GO_ASSET`** until all of the following exist: the exact private DINO snapshot, valid aggregate/per-asset manifests, completed human license review, authenticated preflight receipt, and validated image payload. After those gates, run preflight first, then features. DINO must remain robustness-only and outside the confirmatory family. `claim_allowed=false`.
