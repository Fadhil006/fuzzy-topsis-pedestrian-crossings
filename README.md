# Pedestrian Crossing Intervention Priority with Fuzzy TOPSIS

This is a reproducible Soft Computing assignment package for ranking *feasible improvement packages*, one per verified pedestrian crossing. A higher score means higher relative priority within the candidate set. It does not estimate crash probability or prove that an intervention will reduce crashes.

## Current evidence status

The supplied materials contained a project brief only: no separate instructor handout, starter archive, crossing inventory, observations, costs, or expert review. The proposed study area is the IIIT Kottayam campus and immediately adjoining public-road approaches. No crossing locations or conditions have been asserted. The repository contains an empty field template and a clearly labelled synthetic demonstration. There are **no empirical ranking results**.

The editable report is P20_Fuzzy_TOPSIS_Report.docx. The requirement and evidence audit is in docs/requirements_checklist.csv and docs/audit.md.

## Decision and criteria

The intended reviewers are the campus facilities team and the relevant road authority. Include a crossing only after its location and intervention package are verified; use one feasible package per crossing. Authority and engineering review decide feasibility before ranking.

| Code | Priority-oriented criterion | Unit or scale | Source planned |
| --- | --- | --- | --- |
| P1 | Pedestrian demand | crossing pedestrians/hour | Repeated counts |
| P2 | Motor-vehicle exposure | vehicles/hour | Same count windows |
| P3 | Accessibility deficiency | 0–3 documented audit | Independent assessors and photos |
| P4 | Crossing control or visibility deficiency | 0–3 documented audit | Independent assessors and photos |
| E1 | Essential-destination access, extension | 0–3 defined access importance | Verified destination inventory and walk-network audit |

All are oriented so larger values increase priority. E1 must measure a destination-access consequence that is distinct from pedestrian counts; its classification and walk-network catchment must be published before use. The 0–3 audit scales are proposed study definitions, not claims of Indian code compliance. See docs/collection_protocol.md and docs/data_dictionary.csv.

## Model

For each criterion, a triangular fuzzy number (low, central, high) is built from observed count intervals or documented assessor variation. This triangular shape is a modelling approximation. Its membership grades are not probabilities. Shared criterion bounds (minimum low, maximum high) scale all alternatives to [0,1]. A constant or otherwise identical criterion is excluded and the remaining weights are renormalized. Equal weights are provisional because stakeholder weights have not been elicited.

The calculation uses Chen's triangular vertex distance and **sums** criterion distances. After multiplying each normalized triangle by its crisp criterion weight, the weighted positive ideal is (weight, weight, weight), and the negative ideal is (0,0,0). The weighted ideal and observed-range preprocessing are explicit project adaptations; see docs/method_specification.md. Closeness is distance-to-negative divided by the sum of distances to both ideals. It is a relative decision score.

The crisp baseline applies a separate criterion-wise min–max scale to central values, then takes their equal-weight mean over nonconstant criteria. The research extension adds E1, renormalizes weights, and compares the ranking with the four-criterion model. Weight sensitivity multiplies equal weights by independently sampled factors in [0.8,1.2], renormalizes, and reports top-rank frequency, top-three overlap, and Spearman rank correlation. The synthetic demonstration shows the mechanics only.

## Reproduce

Use Python 3.10 or later. Create a project-local environment (also avoids Arch
Linux's externally managed system-Python restriction) and install dependencies:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

Run the labelled demonstration and the mathematical checks:

    python src/run_project.py --demo
    python -m unittest discover -s tests -v

After field collection, complete one collated row per eligible or rejected candidate in a copy of data/raw_observation_template.csv. Preserve underlying counts in data/count_intervals_template.csv and independent audit forms in data/audit_assessments_template.csv. The collated CSV must contain the required metadata, evidence IDs, all five low/central/high ranges, and an eligibility status. Then run:

    python src/run_project.py --input data/my_completed_observations.csv --output-dir results/field_run

The command rejects missing or invalid values, excludes rejected candidates, saves the clean eligible matrix and processing log, and writes base, crisp, extension, comparison, sensitivity, and SVG chart outputs. It never replaces missing values with zero. Each run needs at least two eligible, distinct crossing packages. Survey-date consistency, photograph validity, local standards, and intervention feasibility still require human review.

## Files and interpretation

- src/model.py: validated fuzzy TOPSIS mathematics.
- src/run_project.py: command-line pipeline and evaluation.
- data/hypothetical_demo.csv and results/hypothetical_*: synthetic illustration only.
- data/raw_observation_template.csv, data/count_intervals_template.csv, data/audit_assessments_template.csv: forms for future fieldwork.
- docs/source_register.csv: verified literature and data-source register with access and reuse notes.
- docs/worked_example.md: independent two-criterion arithmetic check.
- docs/contribution_log.csv: student contribution log template.

The final screening order cannot establish a budget-optimal portfolio. Obtain engineering review, cost estimates, and independent audit evidence before allocating resources. Do not interpret agreement with a crisp baseline as proof of correctness.

## Public-source-informed synthetic dataset

The preserved snapshot produces **28 hypothetical candidate locations**, selected
from actual mapped OSM road nodes around IIIT Kottayam, with synthetic 1–5
criterion estimates and documented fuzzy ranges. These are not 28 independently
verified crossings. No field measurements or engineering feasibility review are
available. Government portals/research are source context, not crossing-level
calibration. Missing OSM tags mean unknown, not absent. A refreshed extract can
produce fewer candidates; the generator never invents locations to fill a quota.

Run from the repository root after activating `.venv`:

```sh
# Offline reproduction from the preserved public map extract:
python scripts/build_synthetic_dataset.py
python src/run_project.py \
  --synthetic-input data/processed/pedestrian_crossings_fuzzy_topsis.csv \
  --output-dir outputs
python -m unittest discover -s tests -v
```

The final **five-criterion** ranking is `outputs/fuzzy_topsis_results.csv`;
`outputs/synthetic_base_ranking.csv` is the separate four-criterion model.
Weight/uncertainty diagnostics currently describe that four-criterion baseline,
not the final five-criterion ranking. All new outputs are synthetic-labelled and
do not overwrite the original four-row demonstration in `results/`.

Key artifacts:

- `data/raw/`: actual public-source responses, saved query and retrieval metadata.
- `data/source_inventory.csv`: URLs, coverage, intended use, licensing and hashes.
- `data/processed/pedestrian_crossings_fuzzy_topsis.csv`: complete synthetic input,
  including integer estimates, fuzzy ranges, coordinates and per-row provenance.
- `data/processed/pedestrian_crossings_observed.csv`: empty actual-observation
  template; synthetic values are never copied into it.
- `data/processed/synthetic_generation_manifest.json`: deterministic generation
  seed **20261024**, scope and content hashes.
- `reports/synthetic_data_methodology.md`: exact scoring, candidate selection,
  assumptions, confidence labels and limitations.

Optional source refresh (requires network; a newer map may change the dataset):

```sh
python scripts/fetch_public_sources.py
python scripts/fetch_osm_context.py --refresh
python scripts/fetch_public_sources.py --cached
```

The final cached command updates inventory checksums from the saved bodies and
current OSM metadata without making network requests. Failed OSM refreshes retain
the previous successful snapshot; see `data/raw/osm_fetch_failures.json`.

OSM attribution: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
ODbL 1.0. The dataset is suitable for a reproducible demonstration, **not a validated
real-site safety ranking**. The instructor's actual-data requirement still needs
explicit approval if this synthetic alternative is used for submission. The Word
and PDF reports are not automatically updated to this new experiment.

## Original four-row demonstration exports

Each run now writes 13 files: the clean matrix and preprocessing log; base, crisp and extension rankings; comparison table; weight runs and summary; an SVG chart; uncertainty scenarios; criterion correlations; calculation trace; and a JSON run manifest. The manifest records the input hash, dependency versions, seed and evidence status. Rejection reasons are preserved in the log. All results in this repository remain hypothetical.

Uncertainty scenarios contract widths by factors 0, 0.5 and 1 around the same centers and refit normalization. They test assumptions, not alternative measured datasets. See docs/method_specification.md for non-discriminating scenarios and tie conventions. The calculation trace reconstructs each baseline distance, and criterion correlations flag possible overlap without proving redundancy.

Use docs/field_readiness.md for the remaining empirical work, data/validation_review_template.csv for independent review, and docs/viva_guide.md to prepare a demonstration. Main report text occupies five pages; references and appendices follow separately. Author details, the personal contribution log and instructor-specific formatting still require student input.

To rebuild the Word report after generating the demonstration, install the optional authoring dependency `python-docx` and run `python scripts/build_report.py`. It reads the ranking and comparison exports; the narrative experiment counts describe the documented default 1,000-draw run. Regenerate that default before building the report.
