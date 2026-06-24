# V2 Optional-Stopping Lab

`SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE`

This synthetic smoke simulation is not a benchmark result.
In synthetic smoke simulations, the monitoring path behaves as expected.

- Evidence status: `smoke_only`
- Replicates: `5`
- Budget: `12`
- Alpha: `0.05`

## null

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_width_ci` | 0.600 | 0.600 | 5.67 |
| `naive_running_mean_threshold` | 0.800 | 0.800 | 3.25 |
| `v2_hoeffding_cs` | 0.000 | 0.000 | NA |
| `v2_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## negative_A_better

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_width_ci` | 0.600 | 0.000 | 2.33 |
| `naive_running_mean_threshold` | 1.000 | 0.000 | 2.00 |
| `v2_hoeffding_cs` | 0.000 | 0.000 | NA |
| `v2_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## positive_B_better

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_width_ci` | 1.000 | 0.000 | 2.00 |
| `naive_running_mean_threshold` | 1.000 | 0.000 | 2.00 |
| `v2_hoeffding_cs` | 0.000 | 0.000 | NA |
| `v2_empirical_bernstein_cs` | 0.000 | 0.000 | NA |

## near_zero

| Method | Decision Rate | False-Decision Rate | Avg Units |
|---|---:|---:|---:|
| `naive_fixed_width_ci` | 0.200 | 0.000 | 2.00 |
| `naive_running_mean_threshold` | 0.600 | 0.000 | 2.00 |
| `v2_hoeffding_cs` | 0.000 | 0.000 | NA |
| `v2_empirical_bernstein_cs` | 0.000 | 0.000 | NA |
