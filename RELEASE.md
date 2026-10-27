# SurveillanceQC v0.1.1rc1 — first public preview

DRAFT FOR REVIEW. Proposed tag: v0.1.1rc1. Proposed GitHub status: prerelease.
Source code is public on GitHub under MIT. This tagged prerelease is not yet published.

SurveillanceQC is a small Python CLI for checking aggregate surveillance count
CSVs before analysis. It produces JSON findings or a readable summary for schema
problems, invalid/negative counts, duplicate identities, invalid periods, missing
observations and interior reporting gaps. A lab-confirmed-versus-total check is
available only with an explicit user-supplied subset rationale.

Inputs remain unchanged; missing values are not imputed as zero. The optional
local research-handoff audit uses explicit workbook-header mappings, preserves
invalid numeric tokens and marks dependent checks incomplete when needed.

Validation: all 48 tests passed from source and against a newly built, installed
wheel on Python 3.12. Local execution used Python 3.12.14; workbook regression
tests used openpyxl 3.1.5. Package metadata requires Python 3.10+, but Python 3.10,
3.11 and all other versions are unverified.

This preview includes source code, tests, documentation and synthetic examples.
It excludes research datasets, workbooks, manuscripts, notebooks and full research
audit reports. Errors indicate violations of a configured contract, not proven
source-agency errors. This is not a validated public-health tool; passing checks
does not establish surveillance accuracy or completeness, and no adoption or
impact is claimed. Code and software documentation are MIT licensed; upstream datasets are excluded.

Install from the repository root with `python -m pip install .`, then run:

```sh
python -m surveillanceqc examples/synthetic_valid.csv --format text
```

Expected: 4 records, 0 errors, 0 warnings. See README.md for full instructions
and limitations. No PyPI publication is part of this release proposal.