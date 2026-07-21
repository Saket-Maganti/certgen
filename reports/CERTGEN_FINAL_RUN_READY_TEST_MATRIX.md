# Final Run-Ready Test Matrix

| Lane | Coverage | State |
|---|---|---|
| Full default suite | all local-safe tests | `258 passed, 4 deselected` |
| Integration audits | subprocess non-integration audit | `4 passed, 258 deselected` |
| Focused core/contract closure | statistical, artifact, runtime, portable, real-closure contracts | `66 passed` |
| Pilot profiles | minimum succeeds; selected CFM/DINO fail; exclusions preserved | pass |
| Study/family freeze | deterministic profile-bound preregistration; canonical six-hypothesis family | pass |
| Extractor adapters | explicit Inception local state dict and CLIP local-only classes | pass (fixtures; real preflight required) |
| Image manifest | canonical fields, safety, hash/decode, legacy rejection | pass |
| Feature packaging | embedded images resolve and decode after ZIP extraction | pass |
| Builder-faithful closure | four builders, three import paths, merge/cache/family/certificate/ranking | pass |
| Analysis contracts | cross-feature, stability, point-vs-certified, compute, gallery | pass |
| Runtime/readiness | measurement taxonomy and separated readiness components | pass |
| Notebooks | five static passes and deterministic regeneration | pass |
| Type/lint/build | compile/import/Ruff/critical mypy/diff/paper | pass; historical full mypy remains 111/34 |
| Audits | notebooks 5/5; registries 7/7; forensic 8/8; V9 22/22; firewalls/scans | pass |
| Portable archive preseal | import; 10 non-Git tests; notebook audit; 21-stage synthetic runtime | pass, 750 members |

No lane uses internet, real CIFAR, real checkpoints, CUDA, or real paper evidence.
