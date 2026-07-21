# R1D Metric Reproduction and Sanity Gate

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`

Status: `BLOCKED_FEATURE_EXTRACTION_NOT_RUN`
Passed: `False`
Claim allowed: `False`

## Feature Cache Checks

- `reference_inception`: `missing` (missing data/features/cifar10_r1/split/reference_inception.npz or data/features/cifar10_r1/split/reference_inception.sidecar.json)
- `google_ddpm_inception`: `missing` (missing data/features/cifar10_r1/split/google_ddpm_inception.npz or data/features/cifar10_r1/split/google_ddpm_inception.sidecar.json)
- `frank_ddpm_ema_inception`: `missing` (missing data/features/cifar10_r1/split/frank_ddpm_ema_inception.npz or data/features/cifar10_r1/split/frank_ddpm_ema_inception.sidecar.json)
- `frank_cfm_inception`: `missing` (missing data/features/cifar10_r1/split/frank_cfm_inception.npz or data/features/cifar10_r1/split/frank_cfm_inception.sidecar.json)
- `reference_clip`: `missing` (missing data/features/cifar10_r1/split/reference_clip.npz or data/features/cifar10_r1/split/reference_clip.sidecar.json)
- `google_ddpm_clip`: `missing` (missing data/features/cifar10_r1/split/google_ddpm_clip.npz or data/features/cifar10_r1/split/google_ddpm_clip.sidecar.json)
- `frank_ddpm_ema_clip`: `missing` (missing data/features/cifar10_r1/split/frank_ddpm_ema_clip.npz or data/features/cifar10_r1/split/frank_ddpm_ema_clip.sidecar.json)
- `frank_cfm_clip`: `missing` (missing data/features/cifar10_r1/split/frank_cfm_clip.npz or data/features/cifar10_r1/split/frank_cfm_clip.sidecar.json)

## Sanity Gates

- `all_features_finite`: `True`
- `no_duplicate_sample_ids_within_role_cache`: `True`
- `inception_feature_dim_stable`: `False`
- `clip_feature_dim_stable`: `False`
- `required_roles_present`: `False`

## Blockers

- feature cache missing: reference_inception
- feature cache missing: google_ddpm_inception
- feature cache missing: frank_ddpm_ema_inception
- feature cache missing: frank_cfm_inception
- feature cache missing: reference_clip
- feature cache missing: google_ddpm_clip
- feature cache missing: frank_ddpm_ema_clip
- feature cache missing: frank_cfm_clip
