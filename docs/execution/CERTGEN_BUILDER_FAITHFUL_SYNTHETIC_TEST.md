# CertGen Builder-Faithful Synthetic Test

`certgen.cvpr.builder_faithful.run_builder_faithful_synthetic` executes the canonical builders with temporary fixture registries and tiny RGB images. It covers profile selection, study freeze, preflight input ZIP, fake output ZIP, secure import, generation input ZIP, subprocess fake generation, secure import, embedded-image feature input ZIP, all-image decode validation, fake feature output ZIP, secure import, cache-v2 merge/validation, family freeze, certificate, and partial ranking.

The test calls `prepare_preflight`, `prepare_generation`, `prepare_features`, and `prepare_family`; it does not construct substitute package configurations. It also uses the production deterministic ZIP and secure importer contracts.

All artifacts are labeled `synthetic_validation_only`, `not_model_evidence`, and `claim_allowed=false`. Passing proves software and lineage continuity only. It does not validate real checkpoints, extractor weights, CUDA behavior, Kaggle dependencies, runtime, or scientific outcomes.
