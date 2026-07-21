# Autorun Status V2: certGen

    Generated: 2026-07-09T14:57:04Z

    Prompt pack: `/Users/saketmaganti/Projects/certGen/certgen_prompt_pack_v8_final_pre_execution`

    Final verdict: `PARTIAL_SUCCESS_BLOCKED_BY_MISSING_INPUTS`

    Status: V8 pre-execution artifacts prepared; final execution audit still blocked by missing CIFAR reference samples.

    Counts:

    - DONE: 5
    - PARTIAL: 5
    - BLOCKED_OR_DEFERRED: 7
    - FAILED: 0
    - READ_ONLY: 2

    Runbooks prepared:

    - `notebooks/kaggle/v8_certgen_cifar10_generation_t4x2_bookrun.ipynb`: CIFAR-10 generation bookrun with T4x2 sharding and output packaging. (Kaggle, T4x2, 30 min-3 hr for 1k/model; longer for 10k/50k)
- `notebooks/kaggle/v8_certgen_cifar10_feature_extraction_t4x2_bookrun.ipynb`: Feature extraction with role-cache hardening. (Kaggle, T4x2, 45-180 min for 1k/model)
- `notebooks/kaggle/v8_checkpoint_preflight_t4x2.ipynb`: Load checkpoints and generate 1-4 images only before full generation. (Kaggle, T4x2, 10-30 min)
