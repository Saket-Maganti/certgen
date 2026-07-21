# CertGen CVPR Canonical Architecture

`certgen.cvpr` owns stage/run/family/preregistration/certificate/ranking contracts; `certgen.packaging` owns safe ZIP and append-only artifact handling; `certgen.features.cache_v2` owns cache identity; `certgen.notebooks.cvpr_factory` owns deterministic notebook JSON; `certgen.visualization` owns paper-approved figure gates; `certgen.paper` owns claim firewalls. Historical V1-V9 wrappers are compatibility surfaces, not the default architecture. Outputs are atomic, non-overwriting, hash-bound, resumable, and lineage-preserving.
