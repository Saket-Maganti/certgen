# CertGen universal Kaggle account handbook

CertGen’s canonical Kaggle workflow is account-, dataset-, mount-, and filename-agnostic. You may use any Kaggle account, dataset owner/slug, notebook title, uploaded ZIP filename, attached-input name, nesting layout, or downloaded output filename. Do not edit `package_identity.json`, either integrity manifest, or the frozen configuration. `claim_allowed=false`.

## What discovery trusts

The notebooks search `/kaggle/input` and `/kaggle/working` recursively, plus any roots in `CERTGEN_SEARCH_ROOTS`. They impose depth, candidate, archive-member, and expansion-byte limits; do not follow symlinks; inspect ZIP central directories before extraction; verify hashes and membership; and select the one package whose internal package type, stage, study/configuration/run identity, profile, scale, completion status, and integrity manifest match. Filenames, modification times, account names, and dataset slugs are never package identity.

ZIP packages and already-extracted package directories are both valid. Unrelated datasets, old CertGen packages, wrong-stage packages, wrong-study packages, wheelhouses, model caches, screenshots, and notes are ignored. Two exact matches stop with `AMBIGUOUS_MATCHING_PACKAGES`; detach one duplicate or provide a narrower identity requirement. Zero matches stop with `NO_MATCHING_PACKAGE` and a candidate-by-candidate explanation.

## Four equivalent account layouts

All of these synthetic layouts are supported and fixture-tested:

```text
account_alpha: /kaggle/input/certgen-run/input.zip
account_beta:  /kaggle/input/random-slug/deep/nested/foo.zip
account_gamma: /kaggle/input/project-copy/          # already extracted
account_delta: /kaggle/working/manual/renamed-package.zip
```

Each layout may include unrelated datasets and may use a differently named model-asset dataset and wheelhouse. Runtime paths are written only to resolution/run logs; they do not change the scientific identity hash.

## Canonical execution order

1. Select the Kaggle accelerator `GPU T4 x2`—not a single T4 and not a local GPU.
2. Attach the current stage input under any dataset slug and filename. Nested placement is allowed.
3. Choose exactly one dependency mode: `KAGGLE_INTERNET_ON_INSTALL`, `PRIVATE_WHEELHOUSE_OFFLINE`, or `USE_PREINSTALLED_VALIDATED`.
4. For preflight and later stages, attach the private asset dataset under any mount name. Its `asset_manifest.json` must match every required asset ID/revision and every file hash.
5. Run the canonical notebook top to bottom. Source-controlled notebooks have no executed output cells.
6. Download the deterministic run-ID output ZIP. You may rename it and place it in any explicitly searched local directory; do not edit or unpack its contents.
7. Resume locally with:

```bash
CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py \
  --resume --explain --search-root /path/to/downloaded/files
```

The current first notebook is `notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb`; its input package type is `DIAGNOSTIC_INPUT`, dependency mode is `KAGGLE_INTERNET_ON_INSTALL`, and expected output package type is `DIAGNOSTIC_OUTPUT`.

## Local inspection

```bash
python3 -m certgen discover packages --search-root /path --expected-stage diagnostic --json
python3 -m certgen discover reference --search-root /path --expected-kind cifar10_python --json
python3 -m certgen discover assets --search-root /path --asset-id clip__asset --revision <revision> --json
python3 -m certgen discover wheelhouse --search-root /path --profile kaggle_t4x2_features --json
```

Use `--max-depth`, `--max-candidates`, `--maximum-members`, and `--maximum-bytes` only to make limits stricter or to accommodate a reviewed large package. CertGen never crawls the entire user filesystem automatically.

## Dependency and private-asset boundary

The diagnostic uses the minimal `kaggle_t4x2_diagnostic` profile. Active CLIP execution uses Transformers; `timm` and `open-clip-torch` are not required. An offline wheelhouse is discovered through `wheelhouse_manifest.json`, including profile, Python/platform compatibility, required distributions, and wheel hashes. Every resolved environment writes `dependency_report.json`, `dependency_freeze.txt`, `pip_check.txt`, `import_smoke_test.json`, and a restart marker when required.

Public bundles contain no private weights, CIFAR archive, generated images, feature caches, credentials, or empirical results. Outputs remain run-log-only until the existing evidence gates validate real execution.
