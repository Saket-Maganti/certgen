# ICML notebook worker audit

The DINO preflight/features, CIFAR 10k v2 generation/features, and released
sample feature lanes route into source-controlled workers. Generation uses the
registered Diffusers checkpoint worker; feature lanes use sharded extraction;
DINO uses the pinned offline asset validator/adapter. Workers run as bounded
subprocesses with explicit `CUDA_VISIBLE_DEVICES` assignment, resume markers,
and closed output-ZIP validation. Cross-family and unresolved multibench lanes
remain honestly blocked on external source/reference/license contracts.
`claim_allowed=false`.
