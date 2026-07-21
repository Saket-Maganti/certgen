# Final Run-Ready Notebook Readiness

All five canonical Kaggle notebooks were regenerated from `certgen.notebooks.cvpr_factory` and pass static analysis. A second clean generation produced byte-identical files.

The preflight notebook schedules only selected assets, uses dedicated extractor asset workers, and records real smoke/calibration outputs. Generation loads packaged validated snapshots and writes the canonical image manifest. Feature extraction validates every embedded/mounted image before GPU discovery and loads the exact packaged extractor assets. All notebooks retain one active subprocess worker per physical GPU, hash-bound resume, deterministic final ZIP recovery, and `claim_allowed=false`.

This is static and fixture readiness only. Real Kaggle T4x2 execution, real dependency resolution, real asset loading, throughput, and VRAM remain untested until preflight.
