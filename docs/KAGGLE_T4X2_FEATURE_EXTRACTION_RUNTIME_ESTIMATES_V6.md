# Kaggle T4x2 Feature Extraction Runtime Estimates V6

`planning estimates only, not empirical project results`

If notebooks record real wall time, mark it as `run_log_only`.

| Scale | Inception | CLIP | Merge/validation | Notes |
|---|---:|---:|---:|---|
| 1k/model plus reference test split | ~5-30 min | ~10-45 min | minutes | depends on IO/model setup |
| 10k/model | ~10-60 min | ~30-120 min | minutes | planning estimate |
| 50k/model | ~30-180 min | ~1-6 hr | minutes to tens of minutes | planning estimate |

Feature extraction outputs are cache artifacts only. They are not paper evidence until local validation, metric/sanity gates, and certificate gates pass.
