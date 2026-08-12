# Expected-input identity bootstrap audit

Result: **PASS**. A successful ICML input build now emits three operator artifacts: the exact authenticated input ZIP, `certgen_icml2027_<lane>_LAUNCH_EXACT.ipynb`, and `certgen_icml2027_launch_manifest.v1.json`. The exact notebook embeds the content-derived expected identity. The generic source-controlled notebook may discover the generated launch manifest recursively. Neither path reads `CERTGEN_EXPECTED_ICML_INPUT_IDENTITY_JSON` or asks an operator to invent JSON.

The stdlib-only pre-import cell validates the identity self-hash, lane, input ZIP SHA-256, exact package-manifest SHA-256, frozen configuration, source-tree inventory, prerequisite set, and worker-spec hash. Discovery is mount-name independent, permits renamed/nested inputs, deduplicates byte-identical copies, and rejects ambiguity, wrong SHA/lane/configuration, stale launch manifests, traversal, links, and unsafe archives.

Evidence: deterministic notebook regeneration passed; bootstrap mutation tests cover renamed/nested ZIPs, identical duplicates, wrong SHA, wrong lane, a stale generic launch manifest, and absence of the old environment variable. `claim_allowed=false`.
