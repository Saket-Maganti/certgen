# Final 100% Pre-Run Test Matrix

Baseline: 258 default tests passed with 4 integration tests deselected. Final: 263 default tests passed with 4 integration tests deselected; the separate integration lane passed 4/4. Focused repair checks for the builder-faithful rehearsal, certificate route, CLIP asset loading, and next-action compatibility pass. The portable archive ran its exact manifest lane (10 passed), 5/5 notebook static checks, and the complete builder-faithful rehearsal. No test uses network, real CIFAR, CUDA, or real model weights.

| Lane | Pre-audit status |
|---|---|
| Worker identity | PASS |
| Reference/control builders | PASS via complete fixture rehearsal |
| Certificate-input/family operational | PASS via complete fixture rehearsal |
| Artifact-driven next action | PASS plus legacy compatibility tests |
| Certificate/lineage/ranking provenance | PASS |
| CLIP release boundary | PASS focused tests |
| Full default | PASS, 263 passed / 4 deselected |
| Integration audit | PASS, 4 passed / 263 deselected |
| Statistical focused lane | PASS, 30 passed |
| Runtime/closure/final focused lane | PASS, 32 passed |
| Notebook static/deterministic | PASS, 5/5 and byte-identical |
| Ruff / critical mypy | PASS / PASS (39 source files) |
| Full mypy debt | 111 errors in 34 files, unchanged historical debt |
| CVPR / forensic / V9 / final audit | PASS 8/8, 8/8, 22/22, 24/24 |
| Paper build / firewall | PASS, 5 pages / PASS |
| Portable archive | PASS, 779 members, 10 tests, 5 notebooks, complete rehearsal |
