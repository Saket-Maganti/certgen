# V2 Feature Cache Contract

`NO_REAL_EVIDENCE`

Feature-cache manifests must record source type, extractor, preprocessing, shape, file hash, source/license status, and evidence status.

Preprocessing matters because FID/KID/CMMD values can change with resize, crop, interpolation, normalization, and feature extractor version. V2 rejects vague preprocessing such as `default` or `unknown`.
