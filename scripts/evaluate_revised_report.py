"""Add transparent crisp reference rankings beside the original evaluation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from evaluate_report import DEFAULT_INPUT, build_evaluation
from model import normalize_priority, validate_weights
from run_project import CRITERIA, load_and_validate, ranks, spearman_scores, triangles_from_frame

DEFAULT_OUTPUT = ROOT / "reports/revised_evaluation"
WORKED_ID = "SYN-OSM-716872373"


def _ranked(ids, scores, **extra):
    table = ranks(ids, scores, "reference")
    return [{"alternative_id": row.alternative_id, "rank": int(row.rank), "score": float(row.score),
             **{key: float(values[ids.index(row.alternative_id)]) for key, values in extra.items()}}
            for row in table.itertuples()]


def _comparison(name, reference, baseline, k):
    ref_order = [row["alternative_id"] for row in reference]
    base_order = [row["alternative_id"] for row in baseline]
    ref_scores = {row["alternative_id"]: row["score"] for row in reference}
    base_scores = {row["alternative_id"]: row["score"] for row in baseline}
    ids = list(ref_scores)
    ref_top = [row["alternative_id"] for row in reference if row["rank"] == 1]
    base_top = [row["alternative_id"] for row in baseline if row["rank"] == 1]
    return {"comparison": name, "top1_changed": set(ref_top) != set(base_top),
            "top_k_overlap": len(set(ref_order[:k]) & set(base_order[:k])) / k,
            "spearman": spearman_scores([base_scores[i] for i in ids], [ref_scores[i] for i in ids]),
            "top1_ids": {"baseline": base_top, "reference": ref_top}}


def _crisp_topsis(values):
    """Standard equal-weight TOPSIS for benefit-oriented central values."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or not values.shape[0] or not values.shape[1] or not np.isfinite(values).all():
        raise ValueError("expected a nonempty finite 2-D matrix")
    minimums, maximums = values.min(axis=0), values.max(axis=0)
    active = maximums > minimums
    if not active.any():
        raise ValueError("no criterion distinguishes the alternatives")
    normalized = np.zeros_like(values)
    normalized[:, active] = (values[:, active] - minimums[active]) / (maximums[active] - minimums[active])
    weights = np.zeros(values.shape[1])
    weights[active] = validate_weights(np.ones(active.sum()))
    weighted = normalized * weights
    positive, negative = weighted.max(axis=0), weighted.min(axis=0)
    d_plus = np.linalg.norm(weighted - positive, axis=1)
    d_minus = np.linalg.norm(weighted - negative, axis=1)
    score = d_minus / (d_plus + d_minus)
    return score, {"normalized": normalized, "weights": weights, "weighted": weighted,
                   "minimums": minimums, "maximums": maximums,
                   "positiveideal": positive, "negativeideal": negative,
                   "distance_positive": d_plus, "distance_negative": d_minus}


def build_revised_evaluation(input_path=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT, draws=1000):
    source, outdir = Path(input_path), Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    primary = build_evaluation(source, outdir / "primary", draws)
    _, frame = load_and_validate(source, synthetic=True)
    ids = frame.alternative_id.tolist()
    values = triangles_from_frame(frame, CRITERIA)[:, :, 1]

    deficiency = values[:, [2, 3]]
    deficiency_norm = normalize_priority(deficiency, ["benefit", "benefit"])
    deficiency_active = np.ptp(deficiency, axis=0) > 1e-12
    # A fully constant deficiency pair has no signal; assign equal scores.
    deficiency_scores = deficiency_norm[:, deficiency_active].mean(axis=1) if deficiency_active.any() else np.full(len(ids), 0.5)
    deficiency_rows = _ranked(ids, deficiency_scores)

    crisp_scores, calc = _crisp_topsis(values)
    crisp_rows = _ranked(ids, crisp_scores, distance_positive=calc["distance_positive"],
                         distance_negative=calc["distance_negative"])

    # Compare additions against primary five-criterion fuzzy TOPSIS, unchanged.
    baseline = [{"alternative_id": row["alternative_id"], "rank": row["rank"], "score": row["score"]}
                for row in primary["all_candidates"]]
    k = min(3, len(ids))
    comparisons = [_comparison("five_criterion_fuzzy_vs_deficiency_rule", deficiency_rows, baseline, k),
                   _comparison("five_criterion_fuzzy_vs_crisp_topsis", crisp_rows, baseline, k)]

    idx = ids.index(WORKED_ID) if WORKED_ID in ids else 0
    worked = {"alternative_id": ids[idx], "rawcentral": values[idx].tolist(),
              **{key: calc[key][idx].tolist() if key in {"normalized", "weighted"} else
                                               (calc[key].tolist() if key in {"weights", "minimums", "maximums", "positiveideal", "negativeideal"}
                                                else float(calc[key][idx]))
                                               for key in ("normalized", "weights", "weighted", "minimums", "maximums",
                                                           "positiveideal", "negativeideal", "distance_positive", "distance_negative")},
              "score": float(crisp_scores[idx])}
    result = {"primary": primary,
              "additional_baselines": {"deficiency_rule": deficiency_rows, "crisp_topsis": crisp_rows,
                                       "comparisons": comparisons},
              "worked_crisp": worked,
              "methods_note": "The primary evaluation, including its original four-central-mean comparison, is preserved. The added deficiency rule and standard crisp TOPSIS are additional computational comparisons on the same 28 inputs, not independent validation."}
    (outdir / "deficiency_rule.csv").write_text(pd.DataFrame(deficiency_rows).to_csv(index=False))
    (outdir / "crisp_topsis.csv").write_text(pd.DataFrame(crisp_rows).to_csv(index=False))
    (outdir / "comparisons.csv").write_text(pd.DataFrame(comparisons).to_csv(index=False))
    (outdir / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--draws", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(build_revised_evaluation(args.input, args.output_dir, args.draws), indent=2))
