# Verification record

Latest implementation verification: 2026-10-24. Source review below was performed on 2026-10-09; no new access dates are claimed.

## Source verification

The Chen (2000) method citation and abstract were checked at its publisher DOI. Battistini et al. (2023) were checked against the University of Bologna publication record and open article entry. Majumdar et al. (2021) and Alver and Katanalp (2022) were checked against the publisher pages. FHWA treatment and visibility pages were checked directly. OpenStreetMap's official copyright page confirms ODbL reuse conditions. The complete source register distinguishes checked information from data that have not been retrieved. The original Chen article text was not open through the browsing interface, so the report explicitly labels project-specific normalization, crisp weights and weighted ideals as adaptations; the vertex-distance summation and closeness were independently checked against an openly accessible peer-reviewed exposition (Jefmański and Sagan, 2021).

## Mathematical and implementation verification

Eight test cases passed using bundled Python 3.12, including independent two-criterion arithmetic, constant-criterion invariance, benefit/cost orientation, invalid data, end-to-end synthetic exports, whitespace duplicate rejection, large finite weights and reconstruction of distances from the trace. The three new tests failed before implementation and passed after the fixes and additions. A separate read-only code review found no important defects; its scenario-convention documentation finding was resolved. A 1,000-draw seeded run and three width scenarios generated the hypothetical exports. See results/test_results.txt, the runtime versions in results/hypothetical_run_manifest.json and docs/worked_example.md.

## Document and package verification

The rebuilt Word report rendered to six pages: five main-text pages plus one references/appendices page. Every page was visually inspected for clipping, broken tables and missing glyphs. The PDF is a convenience rendering of the editable report. The data templates contain no empirical observations. The HYP dataset and all corresponding analysis files are synthetic. An empirical ranking and independent validation remain pending site data collection. Author details, institutional formatting and actual contribution history require student review.

## Scope of the claim

These checks verify reproducibility and internal mathematical consistency of the stated project model. They cannot verify the condition of any crossing, the suitability of a proposed treatment, the validity of provisional weights, or the real-world value of the destination-access extension.
