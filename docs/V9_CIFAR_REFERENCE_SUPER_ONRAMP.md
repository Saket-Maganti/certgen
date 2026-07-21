# V9 CIFAR Reference Super-Onramp

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`

Status: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`
Claim allowed: `false`

## Exact Next Command

`CIFAR_ARCHIVE_ROOT=data/sources commands/v6_cpu_execution/01b_materialize_reference_from_official_archive.sh`

## Detected Paths
- `data/sources/cifar-10-python.tar.gz` (official_cifar_tarball): official tarball hash and member contract passed

## Rejected Paths

## Accepted Structures

Accepted CIFAR-10 reference structures:

1. Official extracted archive:
   <root>/cifar-10-batches-py/data_batch_1 ... data_batch_5, test_batch
2. Archive directory itself:
   <root>/data_batch_1 ... data_batch_5, test_batch
3. Image folder:
   <root>/test/<class>/*.png or .ppm, optionally train/<class>/*
4. Class folder:
   <root>/<airplane|automobile|...>/*.png or .ppm
5. User-provided ZIP/TAR wrapper:
   a path-safe, resource-bounded container holding the official Python batches
   or the hash-verified official cifar-10-python.tar.gz

No download is performed unless --execute-download is explicitly passed.
