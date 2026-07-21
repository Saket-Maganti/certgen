# V9 Runtime Budget Plan

`planning estimates only, not empirical project results`
`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`

Selected scale: `1k`

| Stage | Estimate |
|---|---|
| `checkpoint_preflight` | 5-20 min on Kaggle T4x2 |
| `generation` | 30 min-3 hr total for three models on Kaggle T4x2 |
| `feature_extraction` | Inception 5-30 min; CLIP 10-45 min |
| `cpu_imports` | seconds-minutes |
| `cpu_sanity_gates` | seconds-minutes |
| `cpu_certificate_pilot` | seconds-minutes after gates pass |
