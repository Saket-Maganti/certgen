# V7 Single File Handoff

Current status: `BLOCKED_MISSING_REFERENCE_SAMPLES`. Next local CPU command: `CIFAR_SEARCH_ROOT=/path/to/cifar bash commands/v7_cpu_execution/01_auto_materialize_cifar_reference.sh`. Next Kaggle step: generation bookrun after reference materialization. Upload generation dataset folder; download generation output zip; then feature extraction zip. Stop on missing reference, failed checkpoint, corrupt zip, invalid feature cache, or any `claim_allowed` promotion. Do not build more scaffolding next; provide CIFAR reference input and run the first Kaggle stage.
