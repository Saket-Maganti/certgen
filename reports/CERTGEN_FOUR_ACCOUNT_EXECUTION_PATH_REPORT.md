# CertGen four-account execution-path report

Status: `FOUR_ACCOUNT_EXECUTION_PATH_PASS`

Rows: `36` across four synthetic accounts, eight input/output discovery lanes, and one complete builder-faithful rehearsal lane per account.

Each account independently executes the 27-stage builder-faithful closure, including real preflight/generation/feature importers, controls, cache merge, gates, certificates, and ranking. The diagnostic copy-back lane is also recursively discovered and imported from its arbitrary filename.
Each input lane also executes the exact stdlib pre-import authenticator, exact expected identity, runtime-only asset resolution into a worker snapshot, and the restart contract. Each output lane checks input-bound package identity, arbitrary renaming, and exact local resume selection.

All account, mount, nesting, upload-name, and copy-back differences are runtime locations only. Scientific identity hashes are invariant per stage and for the complete rehearsal.

Fixtures are `synthetic_validation_only`, `not_real_kaggle_input`, `not_real_kaggle_output`, `not_empirical_evidence`, and `claim_allowed=false`.
