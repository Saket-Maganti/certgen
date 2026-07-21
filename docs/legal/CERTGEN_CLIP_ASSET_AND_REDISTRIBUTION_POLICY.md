# CertGen CLIP Asset and Redistribution Policy

Status: conservative pre-run policy. This document does not grant or infer any license right.

## Policy boundary

- **Private research use:** a researcher may use a CLIP snapshot only under terms they have independently reviewed and accepted.
- **User-provided cache:** the user supplies the exact pinned cache; CertGen records its revision, file hashes, loader contract, and license-review status.
- **Private Kaggle dataset mount:** an offline run may mount that validated cache as a private dataset. The mount is an execution input, not a release artifact.
- **Public code release:** source code, schemas, manifests without weight bytes, and instructions may be distributed under the repository license.
- **Public model-weight redistribution:** not permitted by default. CertGen does not claim that the upstream CLIP model repository grants redistribution rights.

## Enforced default

CLIP weights are not bundled in the public reproducibility archive. The user supplies or privately mounts a validated cache. Asset manifests must record `redistribution_allowed=false`, `public_archive_included=false`, `user_provided=true`, `private_mount_required=true`, the upstream `license_source`, and the honest `license_status` until separately verified permission exists.

The release builder rejects common model-weight suffixes and cache/weight directories. Changing public inclusion requires explicit, independently verified permission and a prospective policy update; a successful private preflight is not redistribution approval.
