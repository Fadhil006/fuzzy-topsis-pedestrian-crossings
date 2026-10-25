# Pedestrian Crossing Intervention Priority with Fuzzy TOPSIS

A reproducible Soft Computing project that demonstrates how Fuzzy TOPSIS can rank a hypothetical improvement package at each pedestrian-crossing candidate. Engineering feasibility has not been established. The scores are relative priorities within a candidate set, not crash probabilities, treatment-effect estimates, or a budget-optimal portfolio.

[GitHub repository](https://github.com/Fadhil006/fuzzy-topsis-pedestrian-crossings)

## Primary report

- [Revised report (Word)](P20_Fuzzy_TOPSIS_Report_Revised.docx)
- [Revised report (PDF)](P20_Fuzzy_TOPSIS_Report_Revised.pdf)
- [Earlier archived report (Word)](P20_Fuzzy_TOPSIS_Report.docx)
- [Earlier archived report (PDF)](P20_Fuzzy_TOPSIS_Report.pdf)

The revised report is the current report. The original report is retained as an earlier version, not the primary submission.

## Authors

Team 034:

- Mohammed Ashar Husain (2024BCS0137)
- Muhamed Fadhil (2024BCS0093)
- Anjo P S (2024BCS0097)

## Evidence and scope

The 28-location dataset is a deterministic synthetic exercise built from actual OpenStreetMap geometry in the preserved extract. It contains 27 mapped road-junction candidates and one mapped crossing candidate. The mapped crossing is unverified; none of the candidates is established as a real, safe, or feasible crossing. All five criteria and their fuzzy ranges are synthetic, generated with seed `20261024`. They are not field observations or validated site findings.

There are no field counts, condition surveys, photographs, engineering feasibility reviews, or empirical rankings. OSM tags and derived indicators provide context for the synthetic generator, not observed criterion values. The project makes no operational safety or intervention-effectiveness claims. See [synthetic data methodology](reports/synthetic_data_methodology.md), [evidence audit](reports/revised_evidence_audit.md), and [submission notes](reports/revised_submission_notes.md).

OpenStreetMap attribution: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0. See `data/source_inventory.csv` for source coverage, reuse notes, and hashes.

## Reproduce

Requires Python 3.10 or later. From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_synthetic_dataset.py
python src/run_project.py \
  --synthetic-input data/processed/pedestrian_crossings_fuzzy_topsis.csv \
  --output-dir outputs
python -m unittest discover -s tests -v
```

The generator uses the preserved local map extract and does not need network access. The CLI command writes the five-criterion synthetic ranking and related outputs under `outputs/`. The older `python src/run_project.py --demo` is a separate, four-row teaching demonstration; it is not pooled with the 28-location dataset. Do not use the synthetic output for real-world decisions.

Optional: rebuild the revised report with `python-docx` and `matplotlib` installed, then run `python scripts/build_revised_report.py`. Rendering Word to PDF is optional and requires a local document-rendering tool; the supplied PDF is included for convenience.

## Method in brief

The four-criterion model covers pedestrian demand, vehicle exposure, accessibility deficiency, and control or visibility deficiency. The extension adds essential-destination access. All criteria are priority-oriented. Triangular fuzzy values are normalized against shared input bounds; non-discriminating criteria are removed and remaining weights renormalized. The model uses Chen-style vertex distances and sums criterion distances. Exact ties share rank, with alternative IDs determining display order. Equal weights are provisional.

The separate crisp TOPSIS and deficiency-only references in the revised evaluation are not the original central-score arithmetic-mean baseline. Diagnostics and results from distinct model variants are kept separate. See [method specification](docs/method_specification.md) and the report appendices for details. Fuzzy membership is not probability, and ranking agreement is not proof of correctness.

## Repository guide

- `src/`: validated model and command-line evaluation pipeline.
- `scripts/`: deterministic synthetic dataset generation, source retrieval, and report/evaluation builders.
- `data/raw/`: preserved public-source responses and retrieval metadata.
- `data/processed/`: generated synthetic input and an empty observed-data template. Synthetic values are not copied into the template.
- `outputs/`: generated five-criterion results; `results/`: separate hypothetical teaching-demo outputs.
- `reports/`: evaluation records, revised report checks, evidence notes, and synthetic-data methodology.
- `docs/`: collection protocol, data dictionary, model specification, worked example, and audit materials.
- `tests/`: model and pipeline tests.

Refresh scripts can access the network and may change source extracts; the documented reproduction path above uses the preserved local extract. Consult `docs/collection_protocol.md` before any future fieldwork. Missing measurements must not be imputed, and feasibility, survey dates, photographs, local standards, and engineering decisions require human review.
