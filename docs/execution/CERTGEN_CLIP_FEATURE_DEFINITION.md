# CertGen CLIP Feature Definition

The pilot uses exactly one CLIP estimand: the 768-dimensional projected image embedding returned by `transformers.CLIPModel.get_image_features`. The adapter class is `CLIPModel`; preprocessing is loaded by `CLIPProcessor` from the exact local snapshot at revision `32bd64288804d66eefd0ccbe215aa642df71cc41`.

The pre-normalization and post-normalization dimensions are both 768. The CLIP vision projection is applied, followed by explicit L2 normalization. This definition is identical in the registry, preflight contract, worker, shard sidecar, cache-v2 sidecar, metric capability registry, and study freeze.

Both model and processor are loaded with `local_files_only=True` from the hash-validated snapshot. The upstream repository does not provide an explicit model-weight license declaration, so the registry records that limitation rather than inventing a license. Real use remains subject to the recorded manual approval/preflight policy.
