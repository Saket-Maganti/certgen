# CertGen Portable Archive Contract

The archive includes README, LICENSE, CITATION metadata, package metadata, canonical notebooks, core code, tests, CVPR registries, required reports, closure report, and run-ready handbook. It excludes Git metadata, raw/private data, local caches, quarantine, bytecode, Mac metadata, and build byproducts.

Verification extracts to a clean directory, checks required paths and privacy, imports the package, runs the portable test lane, runs notebook static validation, exercises output-schema tests and the 21-stage synthetic real-contract path, and records archive SHA-256 and member count. No portable test may require Git, internet, CUDA, real CIFAR, or a real model.
