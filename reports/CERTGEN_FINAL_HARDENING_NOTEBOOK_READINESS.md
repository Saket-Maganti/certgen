# Final Notebook Readiness

`READY_FOR_REAL_KAGGLE_PREFLIGHT_AFTER_REFERENCE_AND_LICENSE_INPUTS`; not real-run validated.

| Notebook | Bootstrap | Asset/network | GPU isolation | Batch/OOM | Resume | Preprocessing proof | Integrity/ZIP | Fixture/static | Real Kaggle | Known risk |
|---|---|---|---|---|---|---|---|---|---|---|
| checkpoint preflight T4x2 | yes | both explicit policies | child subprocesses | smoke calibration | per-model | asset/processor capture | yes | pass/pass | no | real package/auth/license/driver |
| CIFAR generation T4x2 1k | yes | offline validated cache | child subprocesses | real batch + halving | per-sample/shard | n/a | yes | pass/pass | no | adapter/model memory and determinism |
| generic generation T4x2 | yes | offline validated cache | child subprocesses | capability-aware | per-sample/shard | n/a | yes | pass/pass | no | each registered adapter needs real preflight |
| CIFAR feature T4x2 1k | yes | offline extractor cache | child subprocesses | calibrated feature batch fallback | extractor/shard | exact expected=observed | yes | pass/pass | no | real CLIP/DINO processors and memory |
| generic feature T4x2 | yes | offline extractor cache | child subprocesses | calibrated feature batch fallback | extractor/shard | exact expected=observed | yes | pass/pass | no | benchmark/extractor-specific behavior |

All notebooks also contain secure input extraction, disk guard, immutable configuration identity, worker monitoring, atomic status, deterministic copy-back and explicit evidence labels. Static/fixture readiness does not prove Kaggle success.
