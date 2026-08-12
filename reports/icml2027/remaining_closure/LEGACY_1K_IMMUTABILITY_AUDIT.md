# Legacy 1k immutability audit

        Result: **PASS**. Every legacy diagnostic, preflight, 1k notebook, frozen profile, reference plan, pilot link, and frozen 10k-v2 identity file matches the hash captured at starting commit `77460dfe6ee1ae8ea294e6a2c36a98cb88e152b3`.

        | Identity | Path | SHA-256 | Result |
        |---|---|---|---|
        | `diagnostic_notebook` | `notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb` | `cd2a774e98ce4c711afd5ac49ae3bdb6fe94a46ae49b1fc58ea5bb2c4777965d` | PASS |
| `diagnostic_input_zip` | `artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip` | `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d` | PASS |
| `preflight_notebook` | `notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb` | `56553ccc3832c522aa482ed73657e27d82e4dbaa8b7c01a68b2bbb059a8f2b00` | PASS |
| `preflight_input_zip` | `artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip` | `d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f` | PASS |
| `legacy_1k_generation_notebook` | `notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb` | `0dbc5216aeac0c538e52a71548f3b2540d43e4d2f762233e4cc0d977b11a1b56` | PASS |
| `legacy_1k_feature_notebook` | `notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb` | `1ac5d341478d312f9f58be717e9dd005af0746af5122f445d8c72888e81479e5` | PASS |
| `legacy_frozen_profile` | `artifacts/cvpr/study/cifar_integrity_minimal.yaml` | `346f0bea70d94803bd9da2793153496a6b0c1fe839174e8d2049773f5bfcc5ae` | PASS |
| `legacy_reference_draw_plan` | `registry/manifests/cvpr/reference_draw_plan.json` | `27bc56310998dd14fbf06fd096c432f1c21fe2389466a52383df8265468bff6f` | PASS |
| `legacy_pilot_link` | `registry/icml2027/legacy_pilot_link.yaml` | `e31faca64bd6ebd9a7326573f9016378c1028c5826c1bf0192aea88e1598c790` | PASS |
| `cifar_10k_v2_config` | `configs/icml2027/cifar_confirmatory_10k_v2.yaml` | `7d543ddd077edeea20bf29d322916a8d0f531ff05787cb779dc2a35506e85e2d` | PASS |
| `cifar_10k_v2_reference_draw_plan` | `registry/manifests/icml2027/cifar10_reference_draw_plan_10k_v2.json` | `fb3b20684ff7bdea7cef120feec72838706002c309878db5db18aae59988a3b2` | PASS |
| `cifar_10k_v2_seed_manifest` | `registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json` | `031b3e10709b436a96afd6e2f2ad4e398861a71bf315ad107b152b87c9f96704` | PASS |
| `cifar_10k_v2_execution_contract` | `registry/icml2027/cifar_10k_v2_execution_contract_v1.json` | `29f7fb84f12ab6e89b0144ade376e49ed8cb382d7c776b9c113a4b609d14d099` | PASS |

        No legacy study semantics, assets, manifests, or notebooks were modified. The canonical next real action remains the diagnostic ZIP `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d`. `claim_allowed=false`.
