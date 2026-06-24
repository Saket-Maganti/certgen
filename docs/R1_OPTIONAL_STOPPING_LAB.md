# V2 Optional-Stopping Lab

`SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE`

This synthetic smoke simulation is not a benchmark result.
In synthetic smoke simulations, the monitoring path behaves as expected.

- Evidence status: `synthetic_only`
- Replicates: `60`
- Budget: `120`
- Alpha: `0.05`

## null_equal_distance

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 0.383 | 0.383 | 36.09 |
| `naive_running_mean_threshold` | 0.300 | 0.300 | 5.83 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## small_effect_A_better

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 0.933 | 0.017 | 41.96 |
| `naive_running_mean_threshold` | 0.450 | 0.033 | 8.89 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## medium_effect_A_better

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 1.000 | 0.000 | 8.33 |
| `naive_running_mean_threshold` | 1.000 | 0.000 | 6.50 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## heavy_tailed_bounded

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 0.367 | 0.367 | 18.18 |
| `naive_running_mean_threshold` | 0.383 | 0.383 | 6.09 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

This synthetic method diagnostic is not real benchmark evidence.
