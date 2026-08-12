# Generator seed contract audit

- Execution contract: `icml2027_cifar_confirmatory_10k_v2_execution_contract_v1` / `7f0a2899aa9d320076562fb4dda530dada25a9c09bde4da3541ca395ac52d6d2`
- Seed manifest: `registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json` / `875ce5637b2596c5e12cbc3ffc0ee76b19c12282290a4a59b75e5d9daa4853d0`
- Records: `20000`; exact regeneration: PASS; 100,000-identity collision audit: PASS.
- Sample identity remains the immutable v2 SHA-256 policy. Generator RNG uses a separate domain-separated canonical string, SHA-256, first eight bytes, big endian, sign bit cleared, range `[0, 2^63-1]`.
- Any collision hard-fails and requires a new derivation version; it is never retried silently.
- GPU call: `torch.Generator(device=device).manual_seed(generator_seed)`.
- Real workers consume exact authenticated records, never an unrelated integer range. Resume requires the prior manifest and exact checkpoint/seed/image hash.

This is execution semantics layered on frozen v2; the v2 study file was not edited. `claim_allowed=false`.
