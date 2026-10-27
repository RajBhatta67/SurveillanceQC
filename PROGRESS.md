# SurveillanceQC handoff

Current version: **0.1.1rc1**, unpublished release candidate. No GitHub or PyPI
publication. MIT is proposed in LICENSE.proposed; adoption, holder and repository name
review remain pending.

## Completed
- Local Python package/CLI: explicit schema, counts, monthly/annual periods,
  duplicates, missingness, interior gaps and optional documented subset checks.
- Six supplied research CSVs checked without modifying any of 189 extracted
  handoff files; 188 checksum entries and 182 payload manifest entries verified.
- September WHO workbook definitions read directly. New extractor matches the
  archived 24,963-record CSV semantically, not as recovered original code.
- Independently reported robustness gaps reproduced, then fixed: workbook labels
  explicitly map to fields; invalid numeric tokens remain evidence, comparisons
  skip unusable operands, and incomplete checks are marked.
- 48 tests pass on Python 3.12 with optional openpyxl 3.1.5 installed. Seven
  earlier and 12 new adapter/regression tests supplement the 29 core tests.
- Full audit rerun: findings, eligible subset results, comparisons, reconciliation
  counts and extracted-workbook checksum unchanged. No invalid numeric tokens in
  the supplied data; requested numeric/alignment checks complete.
- Source CSVs and generated data projections are excluded from the release candidate.

## Read next
README.md -> docs/ROBUSTNESS_REVIEW.md -> docs/WALKTHROUGH.md.
Historical inventory/investigation: docs/RESEARCH_DATA_CHECK.md.
Actual current audit evidence is separate from the clean candidate in the private
review bundle, under audit/. Package changes are in CHANGELOG.md.

## Resume
python -m pip install -e ".[audit]"
python -m unittest discover -s tests -v
python -m surveillanceqc examples/synthetic_valid.csv --format text
python tools/check_research_handoff.py --handoff /path/to/extracted/handoff --output /path/to/NEW/output --verify-workbook

## Next user step
Explain the four questions at the end of WALKTHROUGH.md in your own words.
Review licensing/name/ownership and candidate before considering publication.

## Limits still open
Historical June 2025 WHO workbooks, FTI cleaning/merge script, original September
converter and complete retrieval history are missing. Exact dataset reuse terms
remain unverified. Only Python 3.12 tested. No claimed external adoption,
public-health validation, research acceptance or impact. Missingness and statistical
patterns do not prove incorrect data or a causal mechanism.

## Public GitHub preparation
README shortened; detailed contract moved to docs/USAGE.md. RELEASE.md is the
proposed prerelease description. REPOSITORY_CONTENTS.md lists exact files.
Only documentation, ignore rules and source-archive manifest changed; no features
or Python implementation/tests changed. Working synthetic commands rechecked.
No repository, tag, GitHub release or PyPI publication created.
