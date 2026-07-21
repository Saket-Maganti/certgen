# Kaggle T4x2 Generation Runtime Estimates V6

`planning estimates only, not empirical project results`

These are planning estimates for `run_log_only` notebook expectations. If the notebook records wall time, those values remain run logs and are not paper evidence.

| Model | 1k samples | 10k samples | 50k samples | Notes |
|---|---:|---:|---:|---|
| `google/ddpm-cifar10-32` | ~10-60 min | ~1-8 hr | ~6-24+ hr | DDPM may be slower |
| `FrankCCCCC/ddpm_ema_cifar10` | ~10-60 min | ~1-8 hr | ~6-24+ hr | scheduler-dependent |
| `FrankCCCCC/cfm-cifar10-32` | ~10-60 min | ~1-8 hr | ~6-24+ hr | first run validates loader |

Total 1k pilot for three models on T4x2: ~30 min-3 hr depending on downloads and sampler speed.

No certificate, metric reproduction, undecided fraction, or paper evidence is produced by generation.
