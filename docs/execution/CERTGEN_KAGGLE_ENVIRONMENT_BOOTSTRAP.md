# Kaggle Environment Bootstrap

Evidence class: `planning_only`; claim permission: `false`.

Every canonical notebook calls `certgen.notebooks.environment_bootstrap` before importing model runtimes. The selected profile checks exact compatible ranges for PyTorch, torchvision, Diffusers, Transformers, Accelerate, Safetensors, Pillow, NumPy, SciPy, scikit-learn, Hugging Face Hub, timm, and OpenCLIP. A compatible environment performs no install. An incompatible environment writes the inspection, install plan, pip log, and resolved lock; installation is permitted only when the frozen run enables network access. A successful install ends with `KERNEL_RESTART_REQUIRED`; the restarted notebook must rerun inspection and fails closed if any requirement remains incompatible.

No bootstrap command downloads checkpoints. Offline mode rejects missing Python packages instead of silently reaching the network. Fixture tests cover compatible, offline-missing, install-failure, restart-required, and failed-revalidation paths.
