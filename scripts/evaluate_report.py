"""Reproducible diagnostics supporting the five-criterion synthetic report."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from model import fuzzy_topsis, intervalize, normalize_priority, vertex_distance
from run_project import (CRITERIA, load_and_validate, ranks, sensitivity,
                         spearman_scores, triangles_from_frame)

DEFAULT_INPUT = ROOT / "data/processed/pedestrian_crossings_fuzzy_topsis.csv"
DEFAULT_OUTPUT = ROOT / "reports/evaluation"
SENSITIVITY_SEED = 20261009
DATA_SEED = 20261024
WIDTH_FACTORS = (0.0, 0.5, 1.0)


def build_evaluation(input_path=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT, draws=1000):
    if draws < 1:
        raise ValueError("draws must be positive")
    source, outdir = Path(input_path), Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    _, frame = load_and_validate(source, synthetic=True)
    ids = frame.alternative_id.tolist()
    raw5 = triangles_from_frame(frame, CRITERIA)
    normalized5 = intervalize(raw5)
    score5, plus5, minus5 = fuzzy_topsis(normalized5, np.ones(5))
    raw4 = raw5[:, :4, :]
    normalized4 = intervalize(raw4)
    score4, _, _ = fuzzy_topsis(normalized4, np.ones(4))
    central4 = raw4[:, :, 1]
    active4 = np.ptp(central4, axis=0) > 1e-12
    crisp_norm = normalize_priority(central4, ["benefit"] * 4)
    crisp = crisp_norm[:, active4].mean(axis=1) if active4.any() else np.zeros(len(frame))
    base_table, crisp_table = ranks(ids, score4, "base"), ranks(ids, crisp, "crisp")
    ext_table = ranks(ids, score5, "extension")
    base_order, crisp_order, ext_order = (t.alternative_id.tolist() for t in (base_table, crisp_table, ext_table))
    k = min(3, len(ids))
    comparisons = []
    for name, other, other_scores in (("base_vs_crisp", crisp_order, crisp), ("base_vs_extension", ext_order, score5)):
        comparisons.append({"comparison": name, "top1_changed": base_order[0] != other[0],
                            "top_k_overlap": len(set(base_order[:k]) & set(other[:k])) / k,
                            "spearman": spearman_scores(score4, other_scores)})

    runs, tops = sensitivity(ids, normalized5, score5, draws=draws, seed=SENSITIVITY_SEED)
    runs.to_csv(outdir / "five_criterion_weight_runs.csv", index=False)
    tops.to_csv(outdir / "five_criterion_weight_summary.csv", index=False)
    uncertainty_rows = []
    for factor in WIDTH_FACTORS:
        adjusted = raw5[:, :, 1:2] + factor * (raw5 - raw5[:, :, 1:2])
        scenario = intervalize(adjusted)
        active = np.ptp(scenario, axis=0).max(axis=1) > 1e-12
        status = "computed"
        if not active.any():
            score, status = np.full(len(ids), 0.5), "non_discriminating_all_tied"
        else:
            score, _, _ = fuzzy_topsis(scenario, np.ones(5))
        uncertainty_rows.append({"width_factor": factor,
                                 "top1_ids": sorted(ids[i] for i, s in enumerate(score) if s == max(score)),
                                 "spearman_vs_full": spearman_scores(score5, score), "status": status})
    pd.DataFrame(uncertainty_rows).to_csv(outdir / "five_criterion_uncertainty.csv", index=False)

    active5 = np.ptp(normalized5, axis=0).max(axis=1) > 1e-12
    weights5 = active5.astype(float) / active5.sum()
    trace_rows = []
    for i, aid in enumerate(ids):
        for j, criterion in enumerate(CRITERIA):
            weighted = normalized5[i, j] * weights5[j]
            trace_rows.append({"alternative_id": aid, "criterion": criterion,
                               "active": bool(active5[j]), "weight": weights5[j],
                               **{f"normalized_{s}": normalized5[i,j,q] for q,s in enumerate(("low","mid","high"))},
                               **{f"weighted_{s}": weighted[q] for q,s in enumerate(("low","mid","high"))},
                               "distance_positive": float(vertex_distance(weighted, np.repeat(weights5[j], 3))),
                               "distance_negative": float(vertex_distance(weighted, np.zeros(3)))})
    pd.DataFrame(trace_rows).to_csv(outdir / "five_criterion_calculation_trace.csv", index=False)

    example_id = "SYN-OSM-716872373" if "SYN-OSM-716872373" in ids else ids[0]
    idx = ids.index(example_id)
    example_criteria = []
    for j, criterion in enumerate(CRITERIA):
        weighted = normalized5[idx, j] * weights5[j]
        example_criteria.append({"criterion": criterion, "raw": raw5[idx,j].tolist(),
                                 "normalized": normalized5[idx,j].tolist(), "weight": float(weights5[j]),
                                 "weighted": weighted.tolist(),
                                 "distance_positive": float(vertex_distance(weighted, np.repeat(weights5[j],3))),
                                 "distance_negative": float(vertex_distance(weighted, np.zeros(3)))})
    btable, ctable = base_table.set_index("alternative_id"), crisp_table.set_index("alternative_id")
    _, demo = load_and_validate(ROOT / "data/hypothetical_demo.csv")
    demo_ids = demo.alternative_id.tolist()
    demo_raw = triangles_from_frame(demo, CRITERIA[:4])
    demo_base, _, _ = fuzzy_topsis(intervalize(demo_raw), np.ones(4))
    demo_crisp_raw = demo_raw[:, :, 1]
    demo_crisp_norm = normalize_priority(demo_crisp_raw, ["benefit"] * 4)
    demo_active = np.ptp(demo_crisp_raw, axis=0) > 1e-12
    demo_crisp = demo_crisp_norm[:, demo_active].mean(axis=1) if demo_active.any() else np.zeros(len(demo))
    demo_ext, _, _ = fuzzy_topsis(intervalize(triangles_from_frame(demo, CRITERIA)), np.ones(5))
    demo_base_table = ranks(demo_ids, demo_base, "base").set_index("alternative_id")
    demo_crisp_table = ranks(demo_ids, demo_crisp, "crisp").set_index("alternative_id")
    demo_ext_table = ranks(demo_ids, demo_ext, "extension").set_index("alternative_id")
    old_demo = [{"alternative_id": aid, "base_score": float(demo_base_table.loc[aid,"score"]),
                 "base_rank": int(demo_base_table.loc[aid,"rank"]), "crisp_rank": int(demo_crisp_table.loc[aid,"rank"]),
                 "extension_score": float(demo_ext_table.loc[aid,"score"]),
                 "extension_rank": int(demo_ext_table.loc[aid,"rank"])} for aid in demo_ids]
    confidence_counts = {}
    for value in frame.confidence:
        for criterion, confidence in json.loads(value).items():
            counts = confidence_counts.setdefault(criterion, {})
            counts[confidence] = counts.get(confidence, 0) + 1
    sensitivity_summary = {"mean_top_k_overlap": float(runs.top_k_overlap.mean()),
                           "min_top_k_overlap": float(runs.top_k_overlap.min()),
                           "mean_spearman": float(runs.spearman_vs_equal.mean()),
                           "min_spearman": float(runs.spearman_vs_equal.min()),
                           "top1_frequencies": [{"alternative_id": r.alternative_id, "top1_count": int(r.top1_count),
                                                 "top1_fraction": float(r.top1_fraction)} for r in tops.itertuples()]}
    summary = {"candidate_count": len(frame), "evidence_status": "public_source_informed_synthetic",
               "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
               "draws": draws, "sensitivity_seed": SENSITIVITY_SEED, "data_seed": DATA_SEED,
               "tie_policy": "exact ties share minimum rank; sensitivity top1 uses deterministic ID-selected rank order, not probability",
               "top_candidates": [{"rank": int(r.rank), "alternative_id": r.alternative_id,
                                   "location_name": str(frame.iloc[ids.index(r.alternative_id)].get("location_name", frame.iloc[ids.index(r.alternative_id)].location_description)),
                                   "score": float(r.score), "base_rank": int(btable.loc[r.alternative_id,"rank"]),
                                   "crisp_rank": int(ctable.loc[r.alternative_id,"rank"])} for r in ext_table.head(10).itertuples()],
               "all_candidates": [{"rank": int(r.rank), "alternative_id": r.alternative_id,
                                   "location_name": str(frame.iloc[ids.index(r.alternative_id)].get("location_name", frame.iloc[ids.index(r.alternative_id)].location_description)),
                                   "score": float(r.score), "base_rank": int(btable.loc[r.alternative_id,"rank"]),
                                   "crisp_rank": int(ctable.loc[r.alternative_id,"rank"])} for r in ext_table.itertuples()],
               "comparisons": comparisons, "sensitivity": sensitivity_summary,
               "uncertainty": uncertainty_rows,
               "worked_example": {"alternative_id": example_id, "criteria": example_criteria,
                                   "score": float(score5[idx]), "distance_positive": float(plus5[idx]),
                                   "distance_negative": float(minus5[idx])},
               "candidate_basis_counts": frame.candidate_basis.value_counts().to_dict(),
               "confidence_counts": confidence_counts,
               "ped_destination_spearman": spearman_scores(raw5[:,0,1], raw5[:,4,1]), "old_demo": old_demo}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--draws", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(build_evaluation(args.input, args.output_dir, args.draws), indent=2))
