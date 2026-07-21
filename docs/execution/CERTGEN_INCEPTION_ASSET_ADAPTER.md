# CertGen Inception Asset Adapter

The primary Inception representation is the 2,048-dimensional final global-average-pool activation before the classifier. The adapter freezes `Inception_V3_Weights.IMAGENET1K_V1`, the Torchvision package version, its official transforms, the weight filename, and every file SHA-256.

Online model-asset access is allowed only during preflight. The preflight adapter places the exact weight file below the canonical asset root and records `layout_type=torchvision_local_weight_file` and `loader_type=torchvision_local_state_dict`. Offline extraction constructs Inception with `weights=None`, loads that validated local state dictionary, replaces `fc` with identity, and never calls an implicit download path.

Extraction fails if the enum, version, snapshot location, inventory, hash, preprocessing, or output dimension differs from the approved preflight manifest. Local fixture tests verify the explicit `torch.load(..., weights_only=True)` path without downloading real weights.
