# CertGen four-account portability report

Status: `FOUR_ACCOUNT_PORTABILITY_PASS`

Rows: `36` across four synthetic accounts, eight input/output discovery lanes, and one complete builder-faithful rehearsal lane per account.

Each account independently executes the 27-stage builder-faithful closure, including real preflight/generation/feature importers, controls, cache merge, gates, certificates, and ranking. The diagnostic copy-back lane is also recursively discovered and imported from its arbitrary filename.

All account, mount, nesting, upload-name, and copy-back differences are runtime locations only. Scientific identity hashes are invariant per stage and for the complete rehearsal.

Fixtures are `synthetic_validation_only`, `not_real_kaggle_input`, `not_real_kaggle_output`, `not_empirical_evidence`, and `claim_allowed=false`.
