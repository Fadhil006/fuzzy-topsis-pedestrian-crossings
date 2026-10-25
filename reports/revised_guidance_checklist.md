# Revised report: guidance audit and completion checklist

Audit opened before rewriting on 25 October 2026. The available guidance is
`/home/fadhil/Downloads/Guidance to submit.docx` (DOCX only; no PDF was available).
Both this guidance and `P20_Fuzzy_TOPSIS_Report.docx` were read completely,
including tables, document relationships and footer text. The original report
will be preserved; the deliverable is `P20_Fuzzy_TOPSIS_Report_Revised.docx`.

## Pre-rewrite audit

| Guidance requirement | Existing evidence and gap | Revision/check required |
|---|---|---|
| Defined decision, users, scope and alternatives | Candidate locations and generic packages exist; operational feasibility unknown | Explain screening purpose and intended campus/road-authority users; do not claim approved engineering packages |
| Precise research question and contribution | E1 comparison exists but narrative is repetitive | State whether destination context changes priority after four original criteria are held fixed; no novelty claim based only on location |
| At least three related papers and method source | References and literature table exist; some evidence is abstract-level | Compare problem, data, method and transfer/validation limits; distinguish reading/access levels honestly |
| Criteria dictionary | Five rules exist; direction/scale and meanings dispersed | Give full names, dimensionless 1 to 5 scale, increasing-priority direction, source and rationale |
| Credible data, exact sources, dates, reuse and compatibility | Saved OSM extract and inventory; public context, not local counts | Separate mapped attributes, derived indicators, synthetic scores and unknowns; retain exact extraction and metadata limitations |
| Alternative inclusion and preprocessing | 28 candidates; duplicate/spacing checks and CLI log exist | Describe road topology, 3 km radius, 80 m spacing, 500 m context, deduplication, rejection/no imputation and scope of simulation eligibility |
| Fuzzy representation and justified bounds | Heuristic widths 1 and 1.5, not measured uncertainty | Explain ordered triples, clipping and confidence categories; disclose lack of calibration once clearly; retain width sensitivity |
| Normalization and constant criteria | Shared outer-bound adaptation is implemented | Provide consistent notation, equations, zero-range and non-discrimination treatment; do not mix variants |
| Weights | Equal provisional weights | Show nonnegative weights, sum one, four-criterion 0.25 and five-criterion 0.20; renormalization after exclusions |
| TOPSIS ideals, distance and closeness | Model equations and numeric example exist | Number readable equations, define high-priority ideals, sum vertex distances, reject zero denominator, explain exact and near ties |
| Research extension | E1 adds proximity context; correlation 0.800621 | Explain controlled four-versus-five comparison and overlap; no verified walking-network or improvement claim |
| Worked calculation and crisp comparison | Complete fuzzy trace; old four-row teaching example | Preserve both; include a genuine project-input crisp baseline calculation rather than copy sample numbers |
| Baselines | Four-criterion central mean and no-extension fuzzy model exist | Preserve existing comparisons; audit whether additional deficiency-only or crisp TOPSIS references are applicable and calculate them explicitly if used |
| Implementation and reproducibility | Scripts, manifests and tests | Identify exact runtime inputs, shapes, versions, generation/sensitivity seeds, source hashes and executable commands |
| Sensitivity | 1,000 five-criterion weight runs and three width scenarios | Retain counts, rank correlations, top-three overlap, tie policy and meaningful figure/captions |
| Validation | Arithmetic/software checks; no independent site validation | State this distinction accurately; do not create expert, field or outcome validation |
| Results and practical implications | Current rankings correct; explanation limited | Interpret tied leaders, P1/P2 trade-off, extension changes and limits on operational/budget decisions |
| Structure and presentation | Required broad sections present; inconsistent table captions and dense inline equations | Follow Abstract, I to VIII, references and appendices; add numbered subsections, captions and consistent citations |
| About four to five main pages | Existing five main pages | Render revised document and check references start after page 4 or 5; put full tables/rules in appendices |
| Acknowledgement and references | Ten cited references; source acknowledgements possible | Acknowledge actual public sources only; normalize reference style without changing bibliographic facts |
| No sample/template material | Earlier archived report retains legacy placeholders; revised report identifies Team 034 and its members | Keep legacy placeholders confined to the archived original; retain old experiment only as a labelled supplementary experiment, not template instructions |
| No em dash or en dash | Both occur throughout existing report and citations | Check all body/table/header/footer/metadata text and figure labels; use standard punctuation and ASCII hyphens where needed |
| Complete submission package | Data, logs, code, dependencies and README exist; contribution log empty | List actual package paths in appendix; identify genuine contributions and any grading/permission questions separately |

## Final audit

| Check | Result and evidence |
|---|---|
| Original title and document preservation | Exact title retained. Original DOCX, PDF, primary input and evaluation were hash-checked as unchanged. |
| Structure, problem and contribution | Abstract; I to VIII; numbered subsections; acknowledgement; ten numbered references; Appendices A to F. Introduction states alternatives, users, locality and the E1 research question. |
| Literature | Table 1 compares four transport studies; method and source references retained. Five relevant DOI metadata records were freshly verified. One fresh DOI request was rate-limited, so prior verified metadata were retained. Full-text reading is incomplete and expressly identified, not invented. |
| Source/data distinctions | Sections III.A to III.C distinguish OSM observations, calculated indicators, synthetic scores and unknown conditions. Source archive date is not misrepresented as HTTP completion time. |
| Criteria and weighting | Table 2 defines all five dimensionless 1 to 5 criteria and directions. Table 3 gives weights and sums for the four- and five-criterion models. Appendix E retains generation rules and adjustments. |
| Preprocessing and fuzzy conversion | Section III.C describes duplicates, coordinates, bounds, missing-value rejection, simulation eligibility and heuristic widths. Normalised triples and full worked values are in Table B1 and exported traces. |
| Method and equations | Six numbered editable Word equations cover normalization, weights, vertex distance, distance sums, closeness and width scenarios. The model adaptation, constant criteria, zero denominators, exact ties and display rounding are explained. |
| Worked examples | Appendix B reproduces all five fuzzy criterion contributions and the original 0.68391959 result. Appendix C adds a separately computed crisp TOPSIS example, 0.82770992. No sample-guide numbers were copied. |
| Extension and baselines | Existing four-criterion fuzzy and central-mean results preserved. Two actual additional comparisons use P3/P4-only mean and conventional five-criterion crisp TOPSIS. Mislabelled mean-rule ranks from the old report were corrected. |
| Results and interpretation | Table 4 and Appendix A retain main scores/ranks; Table 5 preserves original comparisons and labels additions. The interpretation explains the tied leaders and replacement of one top-three member. |
| Sensitivity and figure | Figure 1 preserves 514/486 first-place selections; Table 6 preserves all three width scenarios. Five-criterion scope, overlap, rank correlation and deterministic tie policies are explicit. |
| Validation | Software/arithmetic verification is documented. Lack of independent field/expert/outcome validation is disclosed rather than filled with fictional evidence. |
| Supplementary experiment | Table D1 preserves all four HYP alternatives and their original results, explicitly separate from the main dataset and not described as verified crossing observations. |
| Practical implications | Section VII explains evidence planning, unknown conditions, costs/dependencies, scope limits and the need for review before engineering action. |
| Reproduction/package | Appendix F provides exact commands and paths for raw/cleaned data, logs, code, dependencies, references, evaluation and report artifacts. Team 034 and its three verified members are identified; LMS/topic-selection and genuine contribution items remain separate. |
| Length and layout | Revised DOCX is 10 pages total: five main-text pages and references beginning on page 6, followed by appendices. Equations and table values were checked in the available rendering. |
| Language and punctuation | Rewritten for direct academic explanation. Tests check all document XML text including tables, native equations, metadata, headers and footers for forbidden en/em dashes and known placeholder patterns. |
| Numeric verification | Automated checks compare every numerical result-table cell, the worked calculations and reference labels against generated data. The test suite has 32 tests. Independent review found no blocking factual or numerical issue. |

## External requirements not invented or silently marked complete

Genuine individual contributions and LMS/topic-selection submission remain the
team's responsibility. Earlier archived-report placeholders are legacy content,
not the current revised report.
Some full-paper reading is access-limited. Independent empirical validation and
measured crossing scores are not available; the report is a clearly labelled
simulation rather than a substitute for those observations. Any grading requirement
for non-synthetic data, source redistribution permission or course-specific approval
must be resolved externally. See `revised_submission_notes.md` for the concise handoff. Project repository: https://github.com/Fadhil006/fuzzy-topsis-pedestrian-crossings
