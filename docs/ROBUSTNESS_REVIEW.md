# Focused robustness review — candidate 0.1.1rc1

Two reported defects were reproduced before editing. All original 36 tests
passed while the defects were present, so passing that suite did not establish
coverage of these scenarios.

## Workbook field mapping

The old workbook_comparison used `tuple(derived[0].keys())` to name workbook
values. Reversing the archived CSV columns therefore changed extracted field
meanings and made comparison fail. Values and field names were coupled to an
unrelated file's order.

The replacement `WORKBOOK_FIELDS` maps each reviewed workbook header to its
semantic field, e.g. `Measles \\nclinical` to `measles_clinical` (the workbook
header contains a real newline). `extract_workbook` locates each header, then
reads its corresponding column. Neither extraction nor output column order
uses the archived CSV. Missing, duplicated or unreviewed workbook headers still
fail explicitly; formulas and populated unheaded columns remain rejected.

Tests exercise the complete workbook comparison with reversed CSV dictionaries,
assert identical extracted CSV bytes and hashes, check rearranged workbook
headers, and reject unknown/duplicate headers. Their workbooks are synthetic.

## Invalid numbers and incomplete checks

The old `number` raised on text or nonfinite tokens. Callers used it while
projecting periods, checking eligibility and comparing files, so a token the
core checker could report stopped the surrounding audit.

`parse_number` now returns `NumericValue(status, value)`. Status is `valid`,
`missing`, or `invalid`. Only valid cells carry a Decimal. Syntax follows the
core count parser; whole-number mode also rejects fractional counts. Rates use
finite-number mode, which permits fractions. Negative integers are valid
numbers but still fail the separate nonnegative count rule.

Every invalid numeric token from the six source CSVs is retained in its original
projection and in `evidence/invalid_numeric_values.json`, with source label,
record ordinal, column, raw value and reason. An invalid year/month remains
visible in the original field and produces an invalid qc_period, not a repaired
date. Core INVALID_COUNT/INVALID_PERIOD findings continue to be produced.

Dependent operations behave as follows:

- Eligibility excludes invalid operands or keys; the subset report lists
  skipped_invalid_records and sets analysis_complete=false. coverage_complete
  separately says whether every source record was eligible; ordinary missing or
  negative inputs still limit scope even if execution over eligible rows finishes.
- Alignment excludes invalid/missing keys and lists source records skipped on
  each side. Duplicate valid keys still raise explicitly, preserving the existing
  prohibition on silently overwriting records in a dictionary.
- Numeric comparisons skip invalid operands, retain their raw left/right values
  in skipped_numeric_comparisons, and set analysis_complete=false. Equal invalid
  strings are not declared numerically equal. Blank versus NA remains explicit
  missing equivalence; missing versus zero remains a difference.
- Annual/monthly reconciliation skips a country-year/field if an operand is
  invalid. It does not sum the remaining valid months and call that the total.
  Missing-only monthly series remain undefined. Invalid rates are not counted
  as missing rates. Missing annual operands also make arithmetic incomplete.
- A negative-discarded residual with unavailable operands records null agreement
  and analysis_complete=false, rather than manufacturing a match or mismatch.
- The overall audit analysis_complete is false if any requested numeric/alignment
  operation is incomplete. The audit CLI prints this and exits 1 for an incomplete
  audit, 0 when requested audit operations finish. These exits describe execution
  completeness, not the core CLI's finding threshold. Operational/schema/integrity
  failures still stop the audit; this change is not a blanket exception handler.

The core report's analysis_complete describes parsing/schema execution; it can
be true with INVALID_COUNT findings because the invalid cells were successfully
reported. Source summaries now separately expose audit_analysis_complete, and
comparison/scope statuses explain what could actually be evaluated. A complete
audit is not a statement that data are correct.

Regression tests include text, NaN, infinity, unsupported separators, fractional
counts, malformed calendar keys, invalid rates, missing/zero distinctions, empty
comparisons, and a full six-input synthetic handoff with invalid tokens. That
end-to-end test verifies report generation, raw-token preservation, incomplete
statuses and unchanged input hashes. An empty negative-count evidence table is
also handled, so valid synthetic inputs do not cause an index error.

## Release boundary

The candidate contains code, tests, documentation and synthetic examples only.
No research CSVs/workbooks, notebooks, manuscript files, generated research data
projections or full research audit reports are part of the clean candidate.
The private review bundle carries the audit reports separately. The single real
finding discussed in WALKTHROUGH.md is an explanatory excerpt, not a bundled
data fixture. No publication has occurred; code licensing, public name and
broader Python-version checks remain review items.
