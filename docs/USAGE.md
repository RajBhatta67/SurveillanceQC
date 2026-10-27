# Detailed usage and input contract

## Input contract

UTF-8 (optional BOM), comma-separated CSV with unique, nonblank headers. Default
required columns are `country,period,total_cases,lab_confirmed`. Extra columns
are allowed but not validated. Header names and identity values are exact and
case-sensitive. Counts are nonnegative finite whole numbers: `2`, `2.0`, and
`2e3` are accepted; fractions, thousands separators, NaN, infinity, and text are
errors. Outer whitespace in counts is allowed when parsing.

Default periods are strictly `YYYY-MM`, year 0001–9999 and month 01–12.
`--frequency year` requires `YYYY`. Daily dates, timestamps, epidemiological
weeks, and mixed frequencies are unsupported. Invalid dates at the chosen
monthly/annual granularity are errors; daily date validity is not implemented.

Blank or whitespace-only cells are missing. Other markers are explicit:
`--missing-token NA --missing-token ..`. Markers are case-sensitive after
trimming. **Nothing is imputed or rewritten.** `NA` is otherwise an invalid
count, not an automatically inferred null. Missing key/period cells are errors;
missing count cells are warnings because absence may be intentional.

Map a differently named annual CSV explicitly:

```sh
python -m surveillanceqc my.csv --country Country --period Year --frequency year --count Cases
```

For multiple diseases, age groups, or other strata, include every identity
column, for example `--key-column disease --key-column age_group`. Alternatively
prepare a separate, documented single-series table. Omitting real strata can
produce apparent duplicate keys; review the contract before interpreting them.
Country names are not reconciled against ISO codes or geographic boundaries.
Outer key whitespace is warned about but never removed or merged.

## Findings and severity

| Code | Severity | Meaning |
| --- | --- | --- |
| EMPTY_FILE, INVALID_HEADER, MISSING_COLUMNS | Error | Schema cannot be checked; analysis_complete is false |
| MALFORMED_CSV | Error | Parsing stopped; earlier findings may be partial |
| ROW_WIDTH | Error | Wrong number of fields; this record is skipped |
| MISSING_KEY, MISSING_PERIOD, INVALID_PERIOD | Error | Record identity/period does not satisfy contract |
| INVALID_COUNT, NEGATIVE_COUNT | Error | Value is inconsistent with a count schema |
| DUPLICATE_KEY | Error | Same country, period, and configured strata recur |
| SUBSET_EXCEEDS_TOTAL | Error | Contradiction under the user-declared subset definition only |
| MISSING_COUNT | Warning | An observation cell is missing, not zero |
| PERIOD_GAP | Warning | Periods absent between observations within an exact group |
| KEY_WHITESPACE | Warning | Outer whitespace can split identity values |
| NO_OBSERVATIONS | Warning | Header exists but no data records |

Errors mean violations of the **configured contract**, not proven errors by
the source agency. Revised snapshots, correction deltas, or legitimate repeated
strata may need a different contract. Negative adjustment values are unsuitable
for a raw nonnegative count column; do not use this schema for adjustment series.

Gap checking uses the frequency you choose, considers records with valid
identity/period even if counts are invalid or missing, and never invents a full
country roster or coverage window. It cannot detect wholly absent countries,
leading/trailing missing months, or missing cells in skipped malformed records.
Irregular reporting can explain warnings. No outbreak, trend, lab-share decline,
or count increase is flagged as proof that data are wrong.

## Lab-confirmed versus total

This check is **off by default**, visibly recorded as `skipped_no_definition`.
Enable with `--subset-basis "rationale and source"` only after verifying that:

- lab_confirmed counts cases, rather than samples, tests, or positive specimens;
- lab cases are included in the total, for the same disease/population/strata;
- dates, reporting windows, revisions, and inclusion rules are comparable.

`--lab` and `--total` map names; both must also be configured `--count` columns.
The rationale is saved verbatim; the tool does not verify it or infer definitions
from a column name. Missing/invalid operands skip comparison, with their own
findings. See `docs/SOURCES.md` for the WHO documentation assessment.

## Report and API

JSON includes report/tool versions, input filename and SHA-256 of exact bytes,
configuration, records read, analysis completeness, subset-check status,
error/warning counts, and findings with stable codes, severity, explanation,
record ordinals, columns, and context. Header is record 1; quoted multiline
records occupy one ordinal. Blank physical lines are ignored by Python's CSV
reader, so ordinals need not equal editor line numbers. Group findings may have
empty rows; their context contains group values and gap bounds. Summary counts
count findings, not unique records or missing periods. Source names and group
context can identify places; review reports before sharing.

```python
from surveillanceqc import Config, check_csv
report = check_csv("my.csv", Config(counts=("cases",), frequency="year"))
```

The API raises file/encoding exceptions; the CLI converts them to exit 2 on
stderr. A malformed CSV produces an incomplete structured findings report.

