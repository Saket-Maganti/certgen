
# DINOv2 Kaggle runbook

The robustness lane pins `facebook/dinov2-base` at revision `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, uses `AutoImageProcessor` plus `Dinov2Model`, extracts the CLS token (768 dimensions), and freezes the pinned processor's 256-short-edge resize, 224 center crop, bicubic resampling, RGB conversion, rescaling and ImageNet normalization. The official model card and Hugging Face repository identify Apache-2.0; redistribution remains disabled until human review.

Acquire the exact pinned snapshot into a private Kaggle asset, inventory every file and SHA-256, record license approval, build the preflight input, run the T4 x2 preflight, import its authenticated ZIP, then build/run feature extraction. DINOv2 is robustness-only and not part of the frozen pilot or CIFAR 10k confirmatory family.

`claim_allowed=false`.
