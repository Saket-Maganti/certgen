# V1 FID Policy Report

Implemented:

- FID-like metrics are marked `supports_clean_cs=False`.
- FID rigor status is `descriptive_only`.
- The FID policy gate blocks clean-CS FID requests.
- FD-DINOv2 follows the same descriptive-only policy unless later work proves otherwise.

Remaining for V2:

- Decide whether FID remains descriptive, uses an experimental block path, or receives a watertight proof-backed treatment.
