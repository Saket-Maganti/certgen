# CertGen Real Extractor Preflight Protocol

The canonical preflight covers Inception, CLIP, and the pinned selected DINO implementation. Registry rows remain non-operational until a real imported run proves the exact model revision, processor, observed preprocessing, feature dimension, safe batch size, finite output, and asset manifest.

Each isolated worker validates its local cache, loads processor and model, captures preprocessing from the runtime object, compares it with the frozen expectation, runs deterministic fixture images, checks a finite two-dimensional feature matrix and exact dimension, calibrates ascending batch sizes until the first OOM, records peak VRAM and the last safe batch, unloads, and writes an immutable completion marker.

The required status chain is `EXTRACTOR_ASSET_VALID` → `EXTRACTOR_LOAD_PASS` → `PREPROCESSING_MATCH_PASS` → `FEATURE_SMOKE_PASS` → `EXTRACTOR_PREFLIGHT_PASS`. No extractor is silently downgraded or substituted.
