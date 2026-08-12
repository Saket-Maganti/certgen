# CIFAR 10k v2 freeze

- Study: `icml2027_cifar_confirmatory_10k_v2`
- Config SHA-256: `7d543ddd077edeea20bf29d322916a8d0f531ff05787cb779dc2a35506e85e2d`
- Registry contract hash: `0b77851744d8c6a506cc8530f7fc99a92aa0fefa198c1b64711e1924d944c176`
- Reference plan: `f2ae231aa67b0f3b29995451ae56f7fa0a01b0e2410664022dd024a3cb47804e`
- Sampling: IID with replacement from the fixed empirical CIFAR-10 test population
- Kernel: unit-L2 RBF, fixed gamma 0.5, paired contributions in `[-3,3]`
- Boundary: union-Hoeffding, Bonferroni across two confirmatory feature spaces
- Prefixes: literal prefixes at 100/250/500/1000/2000/5000/10000 with frozen sample-ID hashes

The legacy pilot result had not been inspected when v2 was frozen.
`claim_allowed=false`.
