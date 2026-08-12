# Canonical feature worker-spec audit

Result: **PASS** for `cifar_10k_features`, `dinov2_features`, and `released_sample_features`.

The canonical builder binds study/configuration/seed/sample policy, authenticated source manifests and payload hashes, full source row order, per-shard row order, extractor/model/processor/revision, preprocessing hash, feature layer/dimension/dtype/normalization, authenticated asset inventory, exact extractor × role × shard jobs, and aggregate coverage. CIFAR confirmatory jobs cover Inception and CLIP for model A, model B, and reference. DINO is marked robustness-only and non-confirmatory. Released-sample jobs retain the compatibility-before-family-merge gate.

Fail-closed tests reject wrong extractor revisions, preprocessing/source/order hashes, missing jobs, extra extractors, and DINO confirmatory promotion. Aggregate multipart rehearsals validated every canonical job for all three lanes and imported the payload locally. `claim_allowed=false`.
