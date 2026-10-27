# Official documentation assessment — 2026-10-26 (America/New_York)

No WHO-specific column mapping or real-data fixture is implemented in v0.1.
These sources establish reasons for caution, not compatibility with an unseen
WHO workbook or the author's original research file.

1. WHO Immunization Data: Measles reported cases and incidence
   https://immunizationdata.who.int/global/wiise-detail-page/measles-reported-cases-and-incidence?CODE=Global%26YEAR
   Read the introductory text: annual JRF reporting, historical updates as data
   arrive, and a separate link for provisional monthly measles/rubella data.
   Decision: annual and provisional monthly sources must not be assumed to be
   interchangeable or to share update timing.
2. WHO Measles Outbreak Toolbox, final case classifications (updated Sept 2022)
   https://www.who.int/emergencies/outbreak-toolkit/disease-outbreak-toolboxes/measles-outbreak-toolbox
   Read the laboratory-confirmed, epidemiologically linked, clinically compatible,
   and discarded case definitions. Decision: a generic column called "total"
   does not establish its denominator or relationship to laboratory counts.
3. Provisional monthly portal reached through source 1's official link
   https://immunizationdata.who.int/global?location=&topic=Provisional-measles-and-rubella-data
   Navigation was verified. No exact source workbook, field dictionary, frozen
   version, or dataset-specific reuse permission was established in this build.

Before adding a real example: obtain the exact file and documentation; record
publisher, URL, retrieval date, release/version, checksum, sheet/column mapping,
case versus specimen units, period definition, country/strata coverage, missing
markers, revision rules, and explicit applicable reuse terms. Verify whether
lab-confirmed cases truly form a subset of the chosen total at that same scope.
Keep any source-to-canonical transformation as a separate, reproducible script
that preserves the original and reports its decisions. Do not simply relabel
columns or bundle a file because it is publicly downloadable.
