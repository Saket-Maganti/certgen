# CertGen Pilot Profile Protocol

Pilot membership is chosen prospectively and frozen before any outcome is inspected. `python3 -m certgen profiles list` lists the three canonical profiles; `profiles show <profile>` prints its immutable membership and hash.

`cifar_integrity_minimal` selects the two validated DDPM-family candidates, Inception, CLIP, 1,000 generated images per model, a 1,000-draw reference plan, bounded RBF-MMD, and the registered null, obvious-gap, and checkpoint-variant lanes. It is `pilot_only` and always sets `claim_allowed=false`.

`cifar_integrity_modern` and `cifar_full_candidate` are expansion lanes. They fail closed while selected DINO or CFM rows remain unresolved. Excluded rows remain visible as `REGISTERED_NOT_SELECTED`; builders never substitute them after results.

Prepare the minimum profile with:

```bash
python3 -m certgen prepare preflight --profile cifar_integrity_minimal
```

Explicit selection is supported only when both `--models` and `--extractors` are supplied. The resulting selection is hashed and packaged. Changing membership requires a new profile/study version.
