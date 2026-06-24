# V2 MMD Streams

`NO_REAL_EVIDENCE`

V2 uses linear-time MMD-style contribution streams for sequential certificates because a certificate must monitor a growing stream of bounded units. Quadratic MMD remains useful as a fixed-n diagnostic, while stream contributions feed confidence sequences.

Direction convention:

- negative stream mean: A is closer to the reference;
- positive stream mean: B is closer to the reference.

CMMD is treated as MMD on CLIP-like feature arrays. Tests use synthetic feature fixtures and do not require CLIP extraction.
