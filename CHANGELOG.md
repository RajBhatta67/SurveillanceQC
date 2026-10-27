# Changes

## 0.1.1rc1 — unpublished candidate

- Map workbook header labels explicitly to fields; CSV order no longer affects
  extraction. Validate unreviewed/duplicate headers rather than guessing.
- Preserve invalid numeric tokens in audit evidence. Guard eligibility, period
  conversion, alignment, numeric comparisons, reconciliation and residual checks.
- Report skipped operands/records and check completeness separately from core
  findings; incomplete audit execution returns 1. Keep missing distinct from invalid.
- Handle empty comparison inputs and a valid audit with no negative values.
- Add 12 regression tests (48 total) and a real-finding explanatory walkthrough.
- Existing handoff findings and workbook extraction checksum are unchanged.
- Core finding rules unchanged; report and package version advance to 0.1.1rc1.

The candidate has no bundled research datasets and has not been published.
