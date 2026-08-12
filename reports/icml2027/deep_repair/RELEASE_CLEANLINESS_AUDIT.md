# Release cleanliness audit

The compact generated source release is `dist/certgen_icml2027_deep_repair_source.zip`
with SHA-256 `c507698bcb5240c12dc96f4b008b3c074bb5a04b3ddebee89826160c15c8edd4` and 1019 members.
Fresh extraction/import passed; portable tests report
`36 passed in 6.84s`. The builder excludes macOS metadata,
raw/private/model payloads, caches, quarantine material, nested release ZIPs,
and large raw Monte Carlo records. Recorded manifest paths are repository
relative and the working directory is `.`. `claim_allowed=false`.
