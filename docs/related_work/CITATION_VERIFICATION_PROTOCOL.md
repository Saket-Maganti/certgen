# Citation Verification Protocol V5

`NO_FAKE_CITATIONS`

Every related-work row starts as `citation_status=needs_verification` unless the title, authors, venue, year, and URL or DOI have been checked against a real source.

Rules:

- Do not cite rows marked `needs_verification` as final bibliography entries.
- Do not infer authors, years, venues, or URLs from memory.
- Move a row to `verified` only after recording `verification_source`.
- Keep paper-facing paragraphs conditional until citations are verified.

