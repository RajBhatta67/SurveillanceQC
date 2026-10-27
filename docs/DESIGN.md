# Code decisions and walkthrough

1. `Config` is an immutable declaration of what a row means: identity columns,
   period granularity, numeric columns, missing markers, and optional subset
   rationale. Its validation prevents contradictory mappings before reading data.
2. `check_csv` reads bytes once, hashes them, decodes UTF-8, then parses with the
   standard CSV reader. No code path writes the input or returns a cleaned table.
3. Header problems stop dependent checks rather than generating one misleading
   missing-value error per row. Malformed-width records are reported and skipped.
4. Identity uses exact key strings and an integer period index. Month index
   `year * 12 + month - 1` makes December-to-January adjacency work. A dictionary
   remembers the first row for each full key so duplicate findings name both rows.
5. Numeric parsing distinguishes missing cells, invalid numbers, and negatives.
   Decimal avoids losing integer precision above float's exact range. Accepted
   numeric syntax is explicit; 2.0 and 2e3 represent whole-number counts.
6. Only successfully parsed nonnegative numbers reach the optional subset check.
   Missing total plus positive lab is a missing-value warning, never a fabricated
   total=0 contradiction. The basis string records a user assertion, not proof.
7. Sets of periods per group ignore row order and duplicates. Sorted adjacent
   indexes expose interior gaps in O(n log n) sorting time. Each missing interval
   is one warning with bounds and a count rather than thousands of invented rows.
8. Findings are plain dictionaries with stable codes for scripts and messages for
   people. JSON is deterministic for identical bytes/configuration; no clock or
   machine-specific absolute path is embedded. Version metadata makes changes
   traceable. Hashes establish which file was checked, not its truth or origin.
9. CLI presentation and exit codes are separate from checking. The text formatter
   uses the same report; there is one set of check logic to maintain.

To understand the project, trace the synthetic row `Sample Republic,2024-04,3,5`:
CSV reader -> mapped fields -> valid month -> exact identity -> two valid counts
-> no subset finding by default -> one conditional error if the documented
synthetic subset basis is provided. Neither path changes 3 or 5.

Testing rationale: legitimate zeros, large counts, sharp surges, equality, and
separate strata guard against false positives. Invalid periods, Unicode/BOM,
quoted CSV fields, malformed records, and nonfinite/fractional numbers check
boundary behavior. Missingness/subset tests guard the most consequential logic
mistake: treating absence as zero. CLI tests verify automation behavior.
