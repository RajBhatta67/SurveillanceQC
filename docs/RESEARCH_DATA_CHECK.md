# SurveillanceQC research-data check

Completed on the supplied handoff, October 26, 2026 (New York client date).
These are fresh data-quality checks, not a rerun of research estimates or proof
of surveillance accuracy. No data were downloaded or replaced.

## What was actually included

The ZIP contains real CSV and workbook bytes, not just documentation. Every one
of its 188 SHA256SUMS entries matches. All 182 payload entries in FILE_MANIFEST
also match their recorded hashes and sizes. All 189 extracted files, including
the checksum file itself, had identical before/after hashes.

| Relative to research_v6/ | Rows | Provenance and use |
| --- | ---: | --- |
| baseline/data/measles_rubella_monthly.csv | 22,780 | Original supplied FTI research snapshot, 2012–2025; primary monthly input |
| baseline/data/measles_rubella_yearly.csv | 2,380 | Original supplied FTI research snapshot, 2012–2025; primary annual input |
| baseline/data/measles_rubella_merged.csv | 22,780 | Supplied upstream merged product; not an untouched WHO export |
| source_audit/cases_month.csv | 22,780 | Frozen TidyTuesday reference; distinct bytes and missing markers |
| source_audit/cases_year.csv | 2,382 | Frozen TidyTuesday reference; not a primary-input substitute |
| validation2026/data/who_monthly_2026.csv | 24,963 | Archived derived September 2026 conversion, 2012–2026; original converter missing |
| vaccination/wuenic_mcv_2011_2023.csv | 5,070 | Derived vaccination research subset; percentages are outside the count schema |

The three primary CSVs also match the FTI hashes in the archived repository
verification record. This confirms the supplied bytes against recorded evidence;
this check did not repeat an online repository provenance audit.

Included workbooks: September 2026 `b5efa946-404-table-web-epi-curve-data.xlsx`,
`575c038e-403-table-web-reporting-data.xlsx`,
`de8efe08-451-table-web-mr-elimination.xlsx`, and `vaccination/coverage-data.xlsx`.
The September workbooks are later versions, not the missing June 2025 originals.
The frozen TidyTuesday documentation records a June 12, 2025 WHO retrieval;
individual FTI download dates are unrecorded. Refer to the supplied provenance
document for the pinned repository commits and retrieval evidence.

## Conversion and check scope

The new script is `tools/check_research_handoff.py`. The generic v0.1 engine is
unchanged. This script is a local validation workflow, not a verified universal
WHO import adapter or the original research preparation code.

- Each full CSV projection retains all original fields, count tokens, rows and
  order. It only appends `qc_period` from year/month as `YYYY-MM`, or year as
  `YYYY`. Dates outside the declared calendar domain are marked invalid, never
  repaired. Source rows map directly to projection record ordinals.
- Core checks use `iso3`, not mutable country or region labels, as identity.
  Blank and literal `NA` are explicitly missing; neither is changed to zero.
- Only case/category counts are checked as counts. Population, incidence rates,
  vaccination percentages and categorical elimination status are not passed as
  case counts. This prevents false fractional-number errors.
- Monthly checks include measles suspected, each disease's clinical/linked/lab/
  total counts, and discarded. Annual checks include combined suspected counts,
  the eight disease fields, and discarded_cases. Thus missing-count totals below
  are for those configured fields, not every blank in an annual CSV.
- Each disease's subset check runs ONLY on records with all four disease values
  present, integral and nonnegative. Separate eligible projections and mappings
  retain the original record numbers. Gaps introduced by that filtering are
  ignored; only the full-table gaps are interpreted.
- The subset rationale comes from the supplied original September WHO workbook
  `Read Me!B10` and pinned TidyTuesday dictionary. It is not inferred from a
  column name. The older WHO Excel bytes remain unavailable.
- A separate audit checks clinical + linked + lab = total under the same
  eligibility guard. This identity and annual/monthly reconciliation are new
  audit-script checks, not built-in capabilities of the v0.1 CLI.

Machine-readable `summary.json` records source/output hashes, exact core
configurations, script hash, software versions, comparisons and conversions.
Full core JSON reports and source-record maps are in `reports/` and `evidence/`.
The generated normalized data remain local and are reproducible from the user's
handoff. They are not added as bundled public examples while reuse terms remain
unresolved. Original inputs are never opened for writing.

## Core results, full supplied periods

| Input | Records | Missing count cells (warnings) | Negative count cells (errors under count contract) | Interior gap intervals (warnings) |
| --- | ---: | ---: | ---: | ---: |
| Original monthly | 22,780 | 60,764 | 20 | 1,092 |
| Original annual | 2,380 | 174 | 13 | 60 |
| Original merged, monthly count fields | 22,780 | 60,764 | 20 | 1,092 |
| TidyTuesday monthly | 22,780 | 60,764 | 20 | 1,092 |
| TidyTuesday annual | 2,382 | 174 | 13 | 60 |
| September 2026 derived monthly | 24,963 | 66,466 | 20 | 1,240 |

All six runs completed. None produced missing-column, invalid-header, malformed-
record, invalid-numeric, invalid-period, missing-key or duplicate-key findings.
Counts are findings/cells or gap intervals, not unique affected records. The
original monthly 20 negative cells occupy 14 records; all are measles clinical
or total fields in Bhutan, Indonesia or Sri Lanka. The annual negatives are all
in discarded_cases, one per affected record.

The original monthly gap intervals span 5,789 absent country-month records
between observed endpoints; annual intervals span 134 country-years. The later
monthly intervals span 6,609 country-months. These are absent rows under an
assumed regular schedule, not estimates of missing infections or proof of bad
reporting. Entirely unobserved countries, leading/trailing periods, and missing
cells in existing rows are different forms of missingness. No full reporting
roster or event-date convention is established here.

## Findings investigated

**Negative monthly counts:** the same negative values occur in both frozen
monthly CSV representations and are reproduced in the supplied later WHO
workbook conversion. They were not introduced by the new period projection or
blank/NA handling. They violate a nonnegative case-count contract, but their
cause is unverified. The archived phase code treats these disease-months as
missing for analysis; the new audit retains and flags the original values.
Calling them confirmed reclassification corrections or proven WHO source errors
would go beyond the evidence.

**Negative annual discarded counts:** 13 in the full file, but 12 in 2012–2024.
The extra is Poland 2025 (-8). All 13 equal combined suspected cases minus the
measles and rubella totals. This residual-like pattern suggests an explanation
to investigate; it does not prove whether WHO, an upstream transformation, or
another reporting process generated it. The reference annual CSV agrees on the
values. Detailed rows and residual checks are in `evidence/negative_counts.csv`
and `evidence/annual_negative_residuals.json`.

**Missing counts and annual zeros:** fresh reconciliation reproduces the archived
2012–2024 counts: 84 missing suspected counts, 84 missing discarded counts, and
298 records with a discarded count but no published discarded rate. There are
10 measles and 1,137 rubella annual zero totals without any corresponding
observed monthly total values. These are ambiguous zeros requiring interpretation,
not proven false zeros. A sum is undefined when every monthly value is missing;
it is never substituted with zero. Where monthly values exist, their available
raw sums agree with annual values for all eight disease category/total fields.
Agreement does not establish complete monthly reporting.

**Subset and component checks:** no violations among eligible records. Original
monthly eligibility: 22,618 measles and 7,811 rubella records; 162 and 14,969
respectively are skipped due to absent or invalid disease fields. All 2,380
annual records are eligible for each disease. Later monthly eligibility is
24,800 measles and 8,570 rubella. A pass applies only to eligible records and
these particular internal identities, not overall surveillance accuracy.

**Frozen reference agreement:** all 22,780 monthly keys match on numeric values
and missingness after explicitly interpreting blank versus NA. All monthly
region labels differ (e.g. EMRO versus EMR); these do not create duplicate
identities. The annual reference matches every shared cell on 2,380 keys, with
only two reference-only records: SSD/2012 and SSD/2013. Shared monthly fields of
the supplied merged CSV also match the original monthly CSV. Extra merged
annual context fields were not independently validated by that comparison.

**Later snapshot differs from the original:** 22,747 keys overlap, 33 original
keys are absent from the later file, and 2,216 later keys were not in the original.
Shared records include 462 differences in measles_total and 225 in rubella_total,
plus other count and label changes. These are snapshot differences; no revisions
were silently applied to the original. A later file is not a byte-equivalent
replacement for the original research input.

## September workbook check

A new extractor reads `WEB`, verifies its reviewed 15-column header mapping,
ignores completely empty rows/trailing columns, rejects formulas and unexpected
nonempty trailing columns, and preserves workbook blanks. `Read Me!B12` says
2026-09. `Read Me!B10` directly defines total as clinical + linked + lab-confirmed
cases; it also contains the African-region rubella caveat. This provides
source-specific evidence for the guarded internal consistency checks.

All 24,963 extracted keys match the archived `who_monthly_2026.csv`. No shared
cell differences remain under explicit numeric/missing equivalence. Calendar
keys account for workbook `01` versus CSV `1`; numeric counts may be `8` versus
`8.0`. This is semantic equality, not byte identity and not a recovered original
converter. Both original files remain unchanged. The new extraction is labeled
as newly authored; its checksum and workbook row map are retained.

## Exact missing items and what they block

**No primary research CSV is missing.** These unresolved items remain:

| Item | Status / consequence |
| --- | --- |
| June 12, 2025 `404-table-web-epi-curve-data.xlsx` | Missing historical monthly WHO workbook; cannot verify original Excel bytes or regenerate the June release from Excel |
| June 12, 2025 `403-table-web-reporting-data.xlsx` | Missing historical annual WHO workbook; same limitation |
| FTI upstream cleaning/merge script | Missing; no exact filename recorded. Cannot reconstruct how the merged product, regional labels, or omitted SSD records were produced with original code |
| Original September workbook-to-`who_monthly_2026.csv` converter | Missing; no exact filename recorded. New extractor verifies the available pair but does not recover original implementation |
| Original workbook download scripts/history and exact export URLs/timestamps | Missing beyond supplied manifests/plans; no exact script names recorded |
| Applicable dataset-specific reuse permission for these exact historical files | Unverified. TidyTuesday's repository CC0 file alone does not establish all upstream rights. No real-data fixture is bundled for public release |
| Separate final phase notebook | Absent; phase/*.py is available and sufficient for reading that implementation, so it does not block these QC checks |
| Exact finally submitted manuscript/receipt | Unverified; multiple manuscript versions exist. Does not block QC and does not establish acceptance |

The annual September workbook was included but not used by the archived analysis;
its documented style problem was not treated as a CSV-data error. Vaccination
and elimination workbooks are present and retained, but full clinical/coverage/
status audits are outside this focused count-CSV test. Rates, population validity,
and geography reconciliation remain outside the core runs described above.

## Reproduce

Extract the original user handoff, install the project, then run from the project
directory (replace the handoff path; output must be new and outside the handoff):

```sh
python -m pip install -e .
python -m pip install openpyxl==3.1.5
python tools/check_research_handoff.py --handoff /path/to/SurveillanceQC_Research_Handoff --output /path/to/new_qc_run --verify-workbook
python -m unittest discover -s tests -v
```

Without `--verify-workbook`, the six CSV runs need only the installed package
and Python standard library. Workbook checking uses openpyxl 3.1.5. All 36 tests
pass on Python 3.12 here, including seven new synthetic adapter tests. No archived
research scripts, notebooks, models or simulations were executed. No remote
repository or package publication took place.

## Follow-up robustness rerun: 0.1.1rc1

The earlier assessment above describes the initial 36-test run. The later
focused review reproduced and fixed CSV-order-dependent workbook mapping and
invalid-number aborts. All 48 current tests pass. The full existing-handoff
rerun leaves every finding count, eligible subset result, cross-file comparison,
annual reconciliation count and extracted-workbook checksum unchanged. All
189 extracted original files remain unchanged. No invalid numeric tokens were
present in this handoff, so the new incomplete-check fields report complete
requested execution and zero invalid tokens. Changed behavior on invalid data
is covered by synthetic regression tests, not invented real-data findings.
The workbook mapping now follows semantic header labels rather than requiring
the earlier fixed column order; unreviewed or duplicate labels still fail.
See ROBUSTNESS_REVIEW.md for status semantics and WALKTHROUGH.md for one finding.
