# CertGen Exact Next Action

Status: `BLOCKED_USER_REFERENCE_INPUT_REQUIRED`

## Reason

No accepted CIFAR-10 source was found, and the canonical reference manifest has zero rows. The local statistical and safety repairs do not create reference data.

## Accepted inputs

1. Official `cifar-10-python.tar.gz` with MD5 `c58f30108f718f92721af3b95e74349a` and the expected six batch files.
2. Extracted `cifar-10-batches-py` directory containing `data_batch_1` through `data_batch_5` and `test_batch`; batch content is read through the restricted materializer.
3. A complete CIFAR-10 image tree with exactly ten named classes and a valid 10,000-image test or 50,000-image train split.

No automatic download is performed.

## Searches performed

The final canonical search inspected the supplied roots and their immediate candidate directories:

```text
$HOME/Downloads
$HOME/.cache
$HOME/Library/Caches
$HOME/Projects
data/sources
the repository root
```

An earlier filename/layout scan also searched the project tree and home locations for `cifar-10-python.tar.gz`, `cifar-10-batches-py`, `data_batch_1`, and CIFAR-named directories. No source matched.

The canonical pass accepted 0 of 224 candidates: 207 were unsupported directories, 14 macOS cache directories were inaccessible and recorded rather than treated as evidence, 2 observations were the same empty stale reference manifest through different roots, and `data/sources` was absent. The full rejected-path reasons are in `data/results/v9_cifar_reference_onramp.json`.

## User action

Place the official archive at:

```text
data/sources/cifar-10-python.tar.gz
```

The path is gitignored and the validator will refuse a wrong MD5 or unsafe archive.

## Then run exactly

```bash
python3 -m certgen validate reference \
  --source data/sources/cifar-10-python.tar.gz \
  --explain
```

## Expected output

```text
data/results/v9_cifar_reference_onramp.json
docs/V9_CIFAR_REFERENCE_SUPER_ONRAMP.md
```

## Success condition and transition

The command must exit 0 with:

```text
status_code=READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION
materialization_can_proceed=true
claim_allowed=false
```

After that, `python3 -m certgen next-action --write` must advance to `MATERIALIZE_CIFAR_REFERENCE`. Validation is not materialization and is not empirical evidence.
