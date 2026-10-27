All CSVs in this directory are deliberately SYNTHETIC. Country names, counts,
periods, and findings are invented for software testing. They are unrelated to
Raj's research or any WHO dataset. No real observations are redistributed.

synthetic_valid.csv includes a sharp increase and a declining lab share that
should NOT be flagged. Statistical patterns are not data-quality failures.

For this fixture ONLY, lab_confirmed is defined as a subset of total_cases for
the same fictional population, disease, and period. This supports enabling the
optional subset check; it makes no statement about real datasets.

example-report.json and example-summary.txt are generated from
synthetic_issues.csv with the explicit synthetic subset basis. The root README provides both
commands under “Try the synthetic example”; they produce 5 errors and 2 warnings.
