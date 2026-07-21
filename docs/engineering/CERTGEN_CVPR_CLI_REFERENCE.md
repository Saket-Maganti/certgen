# CertGen CVPR CLI Reference

Use `python3 -m certgen status`, `next-action`, `validate reference`,
`materialize reference`, `freeze-config`, `package preflight|generation|features`,
`import preflight|generation|features`, `validate caches` (or the legacy
`validate-caches` alias), `sanity metric-reproduction --config <frozen.yaml>
--out <new.json>`, `sanity controls --config <frozen.yaml> --out <new.json>`,
`plan-runtime --config <frozen.yaml> --out <new.json>`, `certify`, `rank`,
`analyze`, `figures`, and
`audit notebooks|paper|artifact-registry|registries|cvpr`. Omitting the sanity
configuration reports the current prerequisite blocker. Every command is
nonclaim by default and refuses incompatible, incomplete, changed, or
overwrite-prone artifacts.
