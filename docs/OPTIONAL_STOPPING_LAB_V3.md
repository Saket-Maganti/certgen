# V2 Optional-Stopping Lab

`SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE`

This synthetic smoke simulation is not a benchmark result.
In synthetic smoke simulations, the monitoring path behaves as expected.

- Evidence status: `synthetic_only`
- Replicates: `10`
- Budget: `40`
- Alpha: `0.05`

## null_equal_distance

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 0.300 | 0.300 | 10.00 |
| `naive_running_mean_threshold` | 0.400 | 0.400 | 5.00 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## small_effect_A_better

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 0.500 | 0.100 | 21.00 |
| `naive_running_mean_threshold` | 0.300 | 0.100 | 10.00 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## medium_effect_A_better

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 1.000 | 0.000 | 7.00 |
| `naive_running_mean_threshold` | 1.000 | 0.000 | 6.00 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## heavy_tailed_bounded

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_n_peek` | 0.400 | 0.400 | 13.75 |
| `naive_running_mean_threshold` | 0.500 | 0.500 | 5.00 |
| `certgen_hoeffding_cs` | 0.000 | 0.000 | NA |
| `certgen_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

This synthetic method diagnostic is not real benchmark evidence.
