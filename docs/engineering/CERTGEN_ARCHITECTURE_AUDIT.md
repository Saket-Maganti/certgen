# CertGen Architecture and Code-Quality Audit

Status: `LOCAL_REPAIRS_IMPLEMENTED_REAL_PIPELINE_NOT_EXECUTED`; `claim_allowed=false`.

## Verdict

The repository contains a coherent Python package underneath a large historical V1–V9 shell/report surface. The statistical core and current execution helpers are usable through one canonical module CLI, but the tree is not yet a clean public release and no real pipeline stage has been validated end to end. Historical wrappers were preserved as user-owned context; they are not the recommended interface.

## Live architecture

| Layer | Canonical responsibility | Finding |
|---|---|---|
| `certgen.stats` | bounds, CSs, e-values, reference sampling | union-Hoeffding route repaired; experimental methods demoted |
| `certgen.metrics` | kernels, MMD stream, descriptive metrics | direct `[-3,3]` shared-reference difference implemented |
| `certgen.certs` | certificate construction, family execution, IO | first crossing and real-like gates repaired |
| `certgen.features` | extraction, cache validation/migration, merge/split | extractor identity strengthened; canonical v2 cache contract added; no real cache tested |
| `certgen.generation` | guarded checkpoint registry and sample generation | exact revisions and seed manifests; real load not run |
| `certgen.packaging` | build/validate/import ZIPs and artifact registry | traversal/symlink/bomb/overwrite checks and append-only registry |
| `certgen.data` | CIFAR onramp and materialization | safe official-tar and restricted-pickle path; no source available |
| `certgen.audit` / `certgen.paper` | state, evidence, notebook, release, paper gates | new forensic layer catches legacy false positives |
| `certgen.__main__` | canonical status/validate/import/audit surface | implemented; legacy shell wrappers remain compatible |

## Duplication and simplification

The machine inventory classifies hundreds of V1–V9 reports, prompt packs, commands, and results as historical or generated. They encode prior decisions but are not a maintainable public interface. The repair did not delete them. New work should enter through `python3 -m certgen`, package modules, the three hardened notebooks, and consolidated reports. Do not create V10/V11 wrappers.

Duplicated or weak surfaces that remain:

- several legacy CIFAR detectors/materializers with different acceptance rules;
- multiple feature-manifest/sidecar dialects retained for smoke backward compatibility;
- V1–V9 audit scripts that check artifact existence or strings rather than current semantics;
- repeated YAML/JSON model IDs and paths across historical configs;
- many shell entrypoints that should eventually become thin deprecated calls into the canonical CLI; and
- historical report trees unsuitable for a default source release.

## Repairs

- Added the `certgen` console entry point and canonical module CLI.
- Added typed/validated budget, alpha, kernel gamma, and reference draw-plan contracts.
- Added canonical `certgen.feature_cache.v2` validation and non-destructive migration.
- Required real-like certificates to bind feature hashes, metric specification, reproduction class, reference plan, and cache identity.
- Made ZIP inspection reject traversal, absolute/backslash paths, symlinks, special/executable files, encryption, nested archives, duplicate/case-colliding paths, CRC failures, excessive sizes, and excessive compression ratios.
- Made extraction atomic into a new run directory and refuse overwrite.
- Added an append-only hash-verifying artifact registry.
- Pinned CLIP to an immutable revision and recorded resolved Inception/CLIP identities and dependency versions.
- Repaired notebook concurrency, preflight dependency, revision locks, safe extraction, resume validation, atomic statuses, and integrity manifests.
- Extended `.gitignore` to exclude downloaded sources, imported runs, copied-back outputs, and generated sample/feature payloads while leaving metadata visible.

## Configuration and typing

`CSConfig` and focused dataclasses provide typed statistical settings, but there is no single typed schema spanning every historical YAML/JSON file. The canonical path validates its critical values at runtime. Global static typing remains a debt: baseline mypy reported 111 errors in 34 files without a repository configuration. It mixes missing third-party stubs with real annotations. This audit does not weaken type checking or claim it is clean.

## CI and tests

No repository-hosted CI workflow was found. Local pytest is the source of verified behavior. The recommended lanes are documented in the canonical interface. Default tests are offline/CPU-safe and do not download data or models. Optional real integration must remain explicit and skip with a prerequisite reason.

## Release readiness

The package is not release-ready because source licenses, real artifacts, clean-room installation, type debt, citation metadata, and the final empirical contract remain unresolved. The proposed public surface is in `release/CERTGEN_PUBLIC_RELEASE_MANIFEST.txt`; historical/archive candidates are separated without deletion.

## Stop-building decision

No more broad infrastructure layers are justified. Locally valuable correctness and safety gates are now present. Remaining work is input acquisition, external preflight/execution, real artifact validation, and the empirical study, plus bounded maintenance fixes revealed by those runs.
