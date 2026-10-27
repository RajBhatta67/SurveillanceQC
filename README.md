# SurveillanceQC

A small Python command-line tool for checking aggregate infectious-disease
surveillance count CSVs before analysis. It reports findings against an explicit
schema and leaves the input unchanged.

**Version:** 0.1.1rc1, public source preview on GitHub. 
**Python:** package metadata requires 3.10+; **only Python 3.12 has been tested**
(local runtime: 3.12.14). Python 3.10, 3.11 and other versions are unverified.

## Install

From the repository root, preferably in a virtual environment:

```sh
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
```

The core CLI has no third-party runtime dependencies and makes no network
requests while checking data. `surveillanceqc` and `python -m surveillanceqc`
invoke the same CLI. This candidate is installed from source; no PyPI release
is claimed.

## Try the synthetic example

```sh
python -m surveillanceqc examples/synthetic_valid.csv --format text
```

Expected output:

```text
SurveillanceQC 0.1.1rc1 — synthetic_valid.csv
4 records; 0 error(s); 0 warning(s)
Analysis complete: True
Subset check: skipped_no_definition
Findings assess the configured schema; they do not validate surveillance accuracy.
```

Default columns are `country,period,total_cases,lab_confirmed`; monthly periods
use `YYYY-MM`. Counts must be finite, nonnegative whole numbers. For another
schema, map columns explicitly:

```sh
python -m surveillanceqc my.csv --country Country --period Year --frequency year --count Cases
```

Generate JSON findings from the deliberately flawed synthetic fixture:

```sh
python -m surveillanceqc examples/synthetic_issues.csv > report.json
```

This command intentionally exits **1**, with 4 errors and 2 warnings. Required
columns, invalid/negative counts, duplicate keys and invalid periods produce
errors. Missing counts and interior reporting gaps produce warnings. Exit **0**
means no findings at the chosen threshold; **2** means usage/configuration,
file-access or encoding failure. Use `--fail-on warning` to include warnings in
the failure threshold. Redirect only to a new output file, never the input CSV.

To reproduce the bundled example reports with the synthetic subset definition:

```sh
python -m surveillanceqc examples/synthetic_issues.csv --subset-basis "Synthetic fixture: lab cases are included in total for the same fictional population, disease and month; see examples/README.md" > report-with-subset.json
python -m surveillanceqc examples/synthetic_issues.csv --subset-basis "Synthetic fixture: lab cases are included in total for the same fictional population, disease and month; see examples/README.md" --format text > summary-with-subset.txt
```

These commands intentionally exit **1**, with **5 errors and 2 warnings**.

## Definitions and limitations

- Blank cells remain missing. Add explicit markers with `--missing-token NA`;
  missing values are never automatically zero and data are never corrected.
- Lab-confirmed ≤ total is **off by default**. Enable with `--subset-basis
  "documented rationale and source"` only when definitions establish a subset
  for the same disease, population, period and release. The tool records your
  rationale; it does not verify it.
- Periods are monthly or annual; daily dates, epidemiological weeks and mixed
  frequencies are unsupported. Configure all identity strata with `--key-column`.
- Gap warnings cover absent periods between observed endpoints. They cannot
  establish a full reporting roster, missing countries or leading/trailing gaps.
- Files and findings are held in memory. This targets small aggregate tables,
  not large case-level datasets. No geographic reconciliation or general WHO
  workbook adapter is provided.
- Errors are violations of the configured contract, not proven agency mistakes.
  Statistical patterns are not evidence that data are wrong. Passing checks does
  not establish accuracy, completeness, causal mechanisms or public-health validity.

Only synthetic datasets are included. Research datasets, workbooks and full
research audit reports are excluded. No WHO affiliation, external validation,
adoption or impact is claimed.

## Tests and documentation

```sh
python -m pip install -e ".[audit]"
python -m unittest discover -s tests -v
```

All **48 tests passed on Python 3.12**, from source and against a newly built,
installed wheel. The optional audit extra installs openpyxl 3.1.5; without it,
three workbook regression tests are skipped. No other Python version has been
verified. The separate handoff audit uses files supplied locally by the user.

See [usage](docs/USAGE.md), [design](docs/DESIGN.md),
[robustness fixes](docs/ROBUSTNESS_REVIEW.md), and the
[one-finding walkthrough](docs/WALKTHROUGH.md).

## License and development

Code and software documentation are available under the [MIT license](LICENSE).
This does not grant rights to upstream datasets or third-party material.

AI tools assisted with implementation, tests, documentation, and code review.
The project's research motivation comes from Raj Bhatta's measles/rubella analysis.

