# Reference sampling audit

The confirmatory production mode is
`iid_with_replacement_from_fixed_empirical_population`. The corrected v2 draw
plan contains 10000 prospectively seeded PCG64 draws
from 10000 fixed CIFAR-10 reference IDs. Its plan
SHA-256 is `f2ae231aa67b0f3b29995451ae56f7fa0a01b0e2410664022dd024a3cb47804e` and its file SHA-256 is
`fb3b20684ff7bdea7cef120feec72838706002c309878db5db18aae59988a3b2`.

The shared validator rejects without-replacement finite-population sampling,
adaptive reuse, undeclared reuse, a non-precommitted plan, and plan-hash drift.
Without-replacement status is `EXPERIMENTAL_NOT_SUPPORTED`. `claim_allowed=false`.
