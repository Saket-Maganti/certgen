# R1 Source Selection and Provenance Report

`NO_REAL_EVIDENCE`

Claim allowed: `False`

## Status

R1 CIFAR-10 remains `BLOCKED_MISSING_REAL_SOURCES`.

Three public/free checkpoint sources were verified enough to enter the candidate ledger, but no feature-extraction-ready local sample package exists yet. The selected reference source also remains blocked by missing local files and unresolved dataset-license status. No GPU feature extraction, certificate run, or paper-evidence promotion was performed.

## Local Registry Search

Existing CIFAR-10 registry entries were templates only:

- `registry/candidate_benchmarks_template.csv`: `cifar10_planned`
- `registry/candidate_model_pairs_template.csv`: `cifar10_pair_tbd`
- `registry/templates/candidate_model_pairs_template.csv`: `comparison_tbd`
- `registry/manifests/first_pilot_samples_template.jsonl`: `sample_tbd`

The R1 lock therefore creates concrete CIFAR-10 source-selection artifacts:

- `registry/provenance/cifar10_r1_ledger.csv`
- `registry/manifests/cifar10_r1_samples.jsonl`
- `data/results/r1_source_selection_status.json`

## Selected Source Records

| source_id | role | source type | license status | sample status | use in R1 |
|---|---|---|---|---|---|
| `cifar10_reference_dataset` | reference/null/obvious-gap base | released dataset | `unknown` | blocked: local files absent | Required reference source; license and local materialization still block R1 |
| `google/ddpm-cifar10-32` | model source | checkpoint | `verified_free` Apache-2.0 | blocked: generation needed | Model A for medium/close candidate pairs |
| `FrankCCCCC/ddpm_ema_cifar10` | model source | checkpoint | `verified_free` Apache-2.0 | blocked: generation needed | Model B for close-gap candidate pair |
| `FrankCCCCC/cfm-cifar10-32` | model source | checkpoint | `verified_free` Apache-2.0 | blocked: generation needed | Model B for medium-gap candidate pair |

Source checks used public source pages only. The official CIFAR page verifies the 60,000-image 32x32 split layout, while the Hugging Face CIFAR-10 dataset card currently lists licensing information as needing more information. The Google DDPM and FrankCCCCC model cards list Apache-2.0 licenses; they are checkpoint sources, not verified local generated-sample caches.

## Candidate Model Pairs

| pair_id | role | model_a | model_b | status |
|---|---|---|---|---|
| `cifar10_null_split_reference_vs_reference` | null calibration pair | `cifar10_test_split_a` | `cifar10_test_split_b` | blocked until local CIFAR-10 reference samples and license status are locked |
| `cifar10_reference_vs_corruption_sanity` | obvious-gap sanity pair | `cifar10_reference_samples` | `deterministic_corruption_of_same_reference_samples` | blocked until local CIFAR-10 reference samples exist |
| `google_ddpm_vs_frank_cfm` | medium-gap pair | `google/ddpm-cifar10-32` | `FrankCCCCC/cfm-cifar10-32` | blocked until generated samples are materialized and manifested |
| `google_ddpm_vs_frank_ddpm_ema` | close-gap pair | `google/ddpm-cifar10-32` | `FrankCCCCC/ddpm_ema_cifar10` | blocked until generated samples are materialized and manifested |
| `google_ddpm_preprocessing_sensitivity` | preprocessing-sensitivity pair | primary preprocessing on Google DDPM samples | alternate locked preprocessing on the same samples | blocked until the primary generated samples exist |

## Replacement Candidates

| source_id | status | reason |
|---|---|---|
| `minimal_diffusion_cifar10_released_50k` | blocked pending artifact verification | The repository advertises released CIFAR-10 synthetic images and MIT code, but the Google Drive artifact and asset license were not locally verified in R1. |
| `openai_improved_diffusion_cifar10` | blocked pending concrete artifact verification | Public code is available, but R1 did not verify a concrete CIFAR-10 generated sample artifact. |
| `nvlabs_edm_cifar10` | blocked by license | The repository license is CC BY-NC-SA 4.0, so it is not selected for the public/free R1 lock. |

## Validation Summary

- Provenance ledger: structurally valid for the real-pilot validator, with warnings for unknown CIFAR license, unknown reported metrics, and checkpoint generation still needed.
- Sample manifest: structurally valid when local-file existence is not required; blocked when local files are required.
- License status: checkpoint licenses verified free for the three selected model sources; CIFAR reference license remains unresolved.
- Source/sample count consistency: CIFAR reference count and split are source-verified; generated model sample counts are not claimed as available because samples are not materialized.
- Preprocessing lock readiness: `configs/preprocessing_locks/cifar10_inception_bilinear_299.json` is present and non-template.
- Feature-cache status: missing.
- Metric reproduction status: missing.

## Exact Blocker

No feature-extraction-ready local sample package exists. CIFAR-10 reference sample files are absent locally, the CIFAR reference license status is not fully locked, and selected public checkpoints still require generated sample materialization before Kaggle T4x2 feature extraction.

## Kaggle Feature Extraction

Kaggle feature extraction cannot be run yet.

Kaggle command: `not_ready: source package is not feature-extraction-ready`

## Next Local Validation Command

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.cli.run_cifar10_real_pilot \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --sample-manifest registry/manifests/cifar10_r1_samples.jsonl \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json \
  --feature-cache-dir data/features/cifar10_r1 \
  --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json \
  --out-json data/results/r1_cifar10_status.json \
  --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md
```

## Source URLs

- CIFAR-10 official page: https://www.cs.toronto.edu/~kriz/cifar.html
- CIFAR-10 Hugging Face dataset card: https://huggingface.co/datasets/uoft-cs/cifar10
- Google DDPM CIFAR-10 checkpoint: https://huggingface.co/google/ddpm-cifar10-32
- FrankCCCCC DDPM EMA CIFAR-10 checkpoint: https://huggingface.co/FrankCCCCC/ddpm_ema_cifar10
- FrankCCCCC CFM CIFAR-10 checkpoint: https://huggingface.co/FrankCCCCC/cfm-cifar10-32
- Minimal Diffusion replacement candidate: https://github.com/VSehwag/minimal-diffusion
- NVLabs EDM blocked replacement candidate: https://github.com/NVlabs/edm
