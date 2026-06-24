# R1 CPU Validation (synthetic method diagnostic)

`evidence_status: synthetic_only` `claim_allowed: false` `NO_REAL_EVIDENCE`

This is a non-claim, synthetic method diagnostic and is not paper evidence (no real result). It validates the implemented engine on synthetic bounded streams; audit numbers on real generative models remain TBD until claim-eligible feature caches exist.

## 1. Anytime-valid Type-I control and power (alpha=0.05)

| scenario | method | decided_rate | false_decision_rate | mean_samples_to_decision |
|---|---|---:|---:|---:|
| null_equal_distance | naive_fixed_n_peek | 0.390 | 0.390 | 36.859 |
| null_equal_distance | betting | 0.020 | 0.020 | 75.750 |
| null_equal_distance | hoeffding | 0.000 | 0.000 | n/a |
| small_effect_A_better | naive_fixed_n_peek | 0.960 | 0.025 | 40.417 |
| small_effect_A_better | betting | 0.710 | 0.000 | 82.437 |
| small_effect_A_better | hoeffding | 0.000 | 0.000 | n/a |
| medium_effect_A_better | naive_fixed_n_peek | 1.000 | 0.000 | 12.075 |
| medium_effect_A_better | betting | 1.000 | 0.000 | 35.415 |
| medium_effect_A_better | hoeffding | 0.000 | 0.000 | n/a |

Target: betting/hoeffding `false_decision_rate <= alpha` under the null; naive peeking should exceed it.

## 2. e-BH FDR control (20 comparisons, 50% null)

- mean realized FDP: `0.002` (target <= 0.05); met: `True`
- mean power on true gaps: `1.000`
- mean undecided fraction: `0.499`

## 3. Block-size sensitivity (synthetic feature triplet)

| block_size | num_units | decided | samples_to_decision_units | final_width |
|---:|---:|:--:|---:|---:|
| 1 | 1200 | True | 843 | 0.040 |
| 4 | 300 | False | n/a | 0.144 |
| 16 | 75 | False | n/a | 0.552 |
| 32 | 38 | False | n/a | 1.044 |

_Synthetic diagnostic only; not real benchmark evidence._

