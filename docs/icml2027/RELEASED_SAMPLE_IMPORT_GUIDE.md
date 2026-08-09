
# Released-sample import guide

Prepare source metadata without asserting undocumented sampling semantics. Run `released-samples validate`, build a hash-bound manifest, then import into a new empty directory. Validation rejects traversal, absolute paths, symlinks/special members, duplicate/case-colliding members, non-images, decode failures, membership/count/hash mismatches, and duplicate image content. Sample IDs derive from source/revision/archive/image hashes and ordinal, never from trusted filenames.

Official released samples and locally generated samples require an explicit prospective compatibility judgment before sharing a confirmatory family.

`claim_allowed=false`.
