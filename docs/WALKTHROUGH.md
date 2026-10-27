# One real finding, end to end

This example uses the existing private handoff. The release candidate does not
bundle its source data. The excerpt below is one observed finding, not a
synthetic fixture or a new research result.

## 1. Source record

File within the handoff:
`research_v6/baseline/data/measles_rubella_monthly.csv`.

CSV **record 18930** (header is record 1) has country Bhutan, iso3 BTN, year 2014,
month 8, and `measles_clinical=-14.0`. That same record has `measles_total=-14.0`.
The original source SHA-256 is
`f4900b9706fc9fcbbcc2dc341309bcfbc45852e1369b23e2ae105181e918d4b7`.

Record ordinals follow the CSV reader, not necessarily physical editor lines if
quoted fields span lines or blank physical lines occur. The audit appends
qc_period=2014-08 without filtering or reordering the full-table projection, so
record 18930 still points back to the same source record.

## 2. Commands

From the project directory, with the original handoff extracted alongside the
project under `../SurveillanceQC_Research_Handoff`, create a NEW output directory:

```sh
python tools/check_research_handoff.py --handoff ../SurveillanceQC_Research_Handoff --output ../qc-run --verify-workbook
python -m surveillanceqc ../qc-run/normalized/original_monthly.csv --country iso3 --period qc_period --count measles_clinical > ../negative-count-report.json
```

Install first with `python -m pip install -e ".[audit]"` in a virtual environment.
Adapt the handoff path to your extraction location. Never redirect onto the
input CSV. The first command preserves original bytes and emits projections,
checksums, core reports, source-record maps and investigation outputs. The
second command deliberately checks only the clinical-count field to make this
finding easier to follow; its exit code is **1** because it finds errors. Its
full-table output contains 14 negative-count errors and 1,240 warnings (148
missing clinical counts plus 1,092 gap intervals). Those warning counts do not
mean 1,240 bad records.

## 3. Report

The JSON report includes this finding:

```json
{
  "code": "NEGATIVE_COUNT",
  "severity": "error",
  "message": "Count is negative under the configured count schema.",
  "rows": [18930],
  "columns": ["measles_clinical"],
  "context": {}
}
```

The report hashes the projected CSV. The audit summary separately links its hash
to the original input hash and records the append-only conversion. Check both
when explaining provenance; the projected file is not byte-identical to the
original. The private review evidence contains the executed focused command,
exit code, finding excerpt and full focused report.

## 4. Relevant code

Read these functions in order:

1. `tools/check_research_handoff.py::normalize` and `period_text` retain the
   original fields and append the declared period. They do not fix counts.
2. `src/surveillanceqc/checks.py::check_csv` opens bytes for reading, hashes them,
   validates the configured headers, and enumerates records starting at 2.
3. Its numeric loop distinguishes missing from invalid tokens, uses Decimal for
   whole-number validation, then checks `number < 0`. Decimal('-14.0') is a valid
   whole number with a negative sign, so it becomes NEGATIVE_COUNT, not
   INVALID_COUNT. The helper `add` records the code, severity, record and column.
4. `src/surveillanceqc/cli.py::main` chooses JSON/text presentation and returns
   exit 1 when findings reach the configured threshold. It does not change data.
5. In the surrounding audit, `parse_number` now distinguishes missing, invalid
   and valid numeric values. `eligible` excludes this negative disease-month
   from subset/sum checking. A zero subset-violation count therefore cannot
   certify this record as valid. Skipped counts and coverage_complete explain
   the scope; skipped_invalid_records additionally exposes unusable tokens/keys.
6. The separate workbook path uses `WORKBOOK_FIELDS` and `extract_workbook`.
   Header labels determine semantic fields even if CSV or workbook columns move.

## 5. Interpretation and limits

The defensible statement is: "This supplied record violates the configured
nonnegative case-count schema. Its value is retained and needs investigation."

The same negative appears in the frozen monthly reference and the later WHO
workbook representation. That reduces the likelihood that this particular
value came from our new conversion. It does not establish how it originated.
A reclassification/correction is a possible explanation, not a verified cause.
The historical phase analysis excluded invalid disease-months; this checker
reports the source evidence without applying that analytical decision.

It does not prove WHO made an error, reveal the true count, demonstrate
underreporting, establish a causal mechanism, or validate the research estimates.
Changing -14 to 0 would erase information and invent a replacement observation.

## Explain it back

In your own words, answer these before moving to public release:

1. Why is -14.0 NEGATIVE_COUNT rather than INVALID_COUNT? What would happen to
   an empty value and to the token "oops"?
2. Why can we trace report record 18930 back to the source even though the
   projected CSV has a different hash?
3. If one monthly operand is invalid, why skip its annual comparison rather
   than sum the remaining valid months? What tells a reader the check is incomplete?
4. Why must workbook headers determine field meaning instead of the CSV's
   column order? What does passing an eligible-row subset check fail to establish?

Do not memorize these as claims of sole authorship. Be able to describe the
implementation you reviewed, the assistance used, and its practical limits.
