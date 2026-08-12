# Legacy 1k immutability audit

All ten frozen identities are byte-for-byte unchanged. The canonical real path remains diagnostic → import → preflight → import → 1k generation → import → 1k features → import → CPU certificate/analysis.

| Artifact | Before SHA-256 | After SHA-256 | Result |
|---|---|---|---|
| `diagnostic_notebook` | `cd2a774e98ce4c711afd5ac49ae3bdb6fe94a46ae49b1fc58ea5bb2c4777965d` | `cd2a774e98ce4c711afd5ac49ae3bdb6fe94a46ae49b1fc58ea5bb2c4777965d` | PASS |
| `diagnostic_input_zip` | `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d` | `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d` | PASS |
| `preflight_notebook` | `56553ccc3832c522aa482ed73657e27d82e4dbaa8b7c01a68b2bbb059a8f2b00` | `56553ccc3832c522aa482ed73657e27d82e4dbaa8b7c01a68b2bbb059a8f2b00` | PASS |
| `preflight_input_zip` | `d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f` | `d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f` | PASS |
| `legacy_1k_generation_notebook` | `0dbc5216aeac0c538e52a71548f3b2540d43e4d2f762233e4cc0d977b11a1b56` | `0dbc5216aeac0c538e52a71548f3b2540d43e4d2f762233e4cc0d977b11a1b56` | PASS |
| `legacy_1k_feature_notebook` | `1ac5d341478d312f9f58be717e9dd005af0746af5122f445d8c72888e81479e5` | `1ac5d341478d312f9f58be717e9dd005af0746af5122f445d8c72888e81479e5` | PASS |
| `legacy_frozen_profile` | `346f0bea70d94803bd9da2793153496a6b0c1fe839174e8d2049773f5bfcc5ae` | `346f0bea70d94803bd9da2793153496a6b0c1fe839174e8d2049773f5bfcc5ae` | PASS |
| `legacy_reference_draw_plan` | `27bc56310998dd14fbf06fd096c432f1c21fe2389466a52383df8265468bff6f` | `27bc56310998dd14fbf06fd096c432f1c21fe2389466a52383df8265468bff6f` | PASS |
| `legacy_pilot_link` | `e31faca64bd6ebd9a7326573f9016378c1028c5826c1bf0192aea88e1598c790` | `e31faca64bd6ebd9a7326573f9016378c1028c5826c1bf0192aea88e1598c790` | PASS |
| `cifar_10k_v1_config` | `c1e4996fc3e2c8ec90dbd8d297f667b7f4405056e1ad0221faee5a32abdd0cdd` | `c1e4996fc3e2c8ec90dbd8d297f667b7f4405056e1ad0221faee5a32abdd0cdd` | PASS |

No legacy notebook, input ZIP, study/profile, draw plan, or pilot link was rebuilt. `claim_allowed=false`.
