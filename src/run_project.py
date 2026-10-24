"""Run field or explicitly hypothetical crossing-intervention evaluations."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from html import escape
from pathlib import Path
import numpy as np
import pandas as pd
from model import fuzzy_topsis, intervalize, normalize_priority, rank_dataframe, vertex_distance

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ("ped", "vehicle", "access", "deficiency", "destination")
META = ("alternative_id", "crossing_id", "location_description", "intervention_type",
        "survey_date", "evidence_photo_ids", "feasibility_status")

def columns(name):
    return [f"{name}_{suffix}" for suffix in ("low", "mid", "high")]

def load_and_validate(path):
    """Load one collated row per candidate package; retain excluded rows in the log."""
    df = pd.read_csv(path, dtype={k: str for k in META}, keep_default_na=True)
    needed = list(META) + [c for name in CRITERIA for c in columns(name)]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError("missing columns: " + ", ".join(missing))
    if df.empty:
        raise ValueError("no candidate interventions")
    for col in META:
        if df[col].isna().any() or df[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"missing {col}; record evidence rather than imputing it")
        df[col] = df[col].str.strip()
    if df.alternative_id.duplicated().any():
        raise ValueError("alternative_id must be unique")
    if not df.feasibility_status.isin(["eligible", "rejected"]).all():
        raise ValueError("feasibility_status must be eligible or rejected")
    rejected = df.feasibility_status.eq("rejected")
    if rejected.any() and ("notes" not in df.columns or
                           df.loc[rejected, "notes"].fillna("").str.strip().eq("").any()):
        raise ValueError("rejected candidates require a reason in notes")
    eligible = df.loc[df.feasibility_status.eq("eligible")].copy()
    if len(eligible) < 2:
        raise ValueError("at least two eligible interventions are required")
    if eligible.crossing_id.duplicated().any():
        raise ValueError("use one intervention package per crossing in this design")
    if pd.to_datetime(eligible.survey_date, format="%Y-%m-%d", errors="coerce").isna().any():
        raise ValueError("survey_date must use YYYY-MM-DD")
    for name in CRITERIA:
        cols = columns(name)
        numeric = eligible[cols].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any():
            raise ValueError(f"missing or nonnumeric {name} values")
        a = numeric.to_numpy(float)
        if not np.isfinite(a).all() or (a < 0).any() or (a[:, 0] > a[:, 1]).any() or (a[:, 1] > a[:, 2]).any():
            raise ValueError(f"{name} requires finite nonnegative low <= mid <= high")
        if name in {"access", "deficiency", "destination"} and (a > 3).any():
            raise ValueError(f"{name} ratings must be on the documented 0–3 scale")
        eligible.loc[:, cols] = numeric
    return df, eligible

def triangles_from_frame(frame, criteria):
    return np.stack([frame[columns(name)].to_numpy(float) for name in criteria], axis=1)

def ranks(ids, scores, label):
    table = rank_dataframe(ids, scores, label)
    table.insert(0, "rank", table.score.rank(method="min", ascending=False).astype(int))
    return table

def spearman_scores(first, second):
    """Pearson correlation of average ranks; undefined if either list ties fully."""
    x = pd.Series(first).rank(method="average").to_numpy(float)
    y = pd.Series(second).rank(method="average").to_numpy(float)
    if np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])

def sensitivity(ids, normalized, base_scores, draws=1000, seed=20261009):
    """Perturb equal weights by independent factors in [0.8,1.2], renormalize."""
    rng = np.random.default_rng(seed)
    center = np.ones(normalized.shape[1]) / normalized.shape[1]
    reference = ranks(ids, base_scores, "reference").alternative_id.tolist()
    k = min(3, len(ids))
    records = []
    for run in range(draws):
        weights = center * rng.uniform(0.8, 1.2, size=len(center))
        weights /= weights.sum()
        score, _, _ = fuzzy_topsis(normalized, weights)
        order = ranks(ids, score, "sensitivity").alternative_id.tolist()
        records.append({"run": run + 1, "top1": order[0],
                        "top_k_overlap": len(set(order[:k]) & set(reference[:k])) / k,
                        "spearman_vs_equal": spearman_scores(base_scores, score),
                        **{f"weight_{j+1}": weight for j, weight in enumerate(weights)}})
    runs = pd.DataFrame(records)
    summary = (runs.top1.value_counts().reindex(ids, fill_value=0)
               .rename_axis("alternative_id").reset_index(name="top1_count"))
    summary["top1_fraction"] = summary.top1_count / draws
    return runs, summary

def write_sensitivity_figure(summary, path, title):
    """Save a dependency-free SVG bar chart with labelled frequencies."""
    width, height = 720, 110 + 58 * len(summary)
    bars = []
    for index, row in summary.reset_index(drop=True).iterrows():
        y = 75 + 58 * index
        bar_width = 400 * float(row.top1_fraction)
        bars.append(f'<text x="12" y="{y + 18}" font-size="15">{escape(str(row.alternative_id))}</text>'
                    f'<rect x="150" y="{y}" width="{bar_width:.2f}" height="25" fill="#315f89"/>'
                    f'<text x="{160 + bar_width:.2f}" y="{y + 18}" font-size="14">'
                    f'{row.top1_fraction:.1%}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}">'
           '<rect width="100%" height="100%" fill="white"/>'
           f'<text x="12" y="29" font-size="18" font-weight="bold">{escape(title)}</text>'
           '<text x="150" y="51" font-size="13">Fraction of weight draws ranked first</text>'
           + ''.join(bars) + '</svg>')
    path.write_text(svg, encoding="utf-8")

def evaluate(frame, outdir, prefix="", draws=1000):
    """Write base, crisp, extension, and sensitivity tables for complete data."""
    outdir.mkdir(parents=True, exist_ok=True)
    ids = frame.alternative_id.tolist()
    base = intervalize(triangles_from_frame(frame, CRITERIA[:4]))
    extended = intervalize(triangles_from_frame(frame, CRITERIA))
    base_score, base_plus, base_minus = fuzzy_topsis(base, np.ones(4) / 4)
    ext_score, ext_plus, ext_minus = fuzzy_topsis(extended, np.ones(5) / 5)
    central = triangles_from_frame(frame, CRITERIA[:4])[:, :, 1]
    central_active = np.ptp(central, axis=0) > 1e-12
    # The simple-priority baseline uses its own crisp min-max scale.
    crisp_normalized = normalize_priority(central, ["benefit"] * 4)
    crisp_score = (crisp_normalized[:, central_active].mean(axis=1)
                   if central_active.any() else np.zeros(len(ids)))
    tables = {
        "base_ranking": ranks(ids, base_score, "fuzzy_TOPSIS_base"),
        "crisp_baseline": ranks(ids, crisp_score, "equal_weight_central_mean"),
        "extension_ranking": ranks(ids, ext_score, "fuzzy_TOPSIS_destination_extension"),
    }
    for name, distances in (("base_ranking", (base_plus, base_minus)),
                            ("extension_ranking", (ext_plus, ext_minus))):
        distance_frame = pd.DataFrame({"alternative_id": ids, "distance_positive": distances[0],
                                       "distance_negative": distances[1]})
        tables[name] = tables[name].merge(distance_frame, on="alternative_id")
    base_order = tables["base_ranking"].alternative_id.tolist()
    ext_order = tables["extension_ranking"].alternative_id.tolist()
    crisp_order = tables["crisp_baseline"].alternative_id.tolist()
    k = min(3, len(ids))
    comparisons = pd.DataFrame([
        {"comparison": "base_vs_crisp", "top1_changed": base_order[0] != crisp_order[0],
         "top_k_overlap": len(set(base_order[:k]) & set(crisp_order[:k])) / k,
         "spearman": spearman_scores(base_score, crisp_score)},
        {"comparison": "base_vs_extension", "top1_changed": base_order[0] != ext_order[0],
         "top_k_overlap": len(set(base_order[:k]) & set(ext_order[:k])) / k,
         "spearman": spearman_scores(base_score, ext_score)},
    ])
    tables["comparisons"] = comparisons
    runs, summary = sensitivity(ids, base, base_score, draws=draws)
    tables["weight_sensitivity_runs"] = runs
    tables["weight_sensitivity_summary"] = summary
    # Contract widths around the same central observations; these are scenarios,
    # not newly collected evidence. Refit bounds consistently in every scenario.
    raw = triangles_from_frame(frame, CRITERIA[:4])
    scenarios = []
    for factor in (0.0, 0.5, 1.0):
        adjusted = raw[:, :, 1:2] + factor * (raw - raw[:, :, 1:2])
        normalized = intervalize(adjusted)
        if not (np.ptp(normalized, axis=0).max(axis=1) > 1e-12).any():
            score = np.full(len(ids), .5)
            status = "non_discriminating_all_tied"
        else:
            score = fuzzy_topsis(normalized, np.ones(4))[0]
            status = "computed"
        table = ranks(ids, score, "uncertainty_width_scenario")
        table["width_factor"] = factor
        table["status"] = status
        table["spearman_vs_base"] = spearman_scores(base_score, score)
        scenarios.append(table)
    tables["uncertainty_sensitivity"] = pd.concat(scenarios, ignore_index=True)
    active = np.ptp(base, axis=0).max(axis=1) > 1e-12
    weights = active.astype(float) / active.sum()
    trace = []
    for i, alternative in enumerate(ids):
        for j, criterion in enumerate(CRITERIA[:4]):
            weighted = base[i, j] * weights[j]
            trace.append({"alternative_id": alternative, "criterion": criterion,
                          "active": bool(active[j]), "weight": weights[j],
                          **{f"normalized_{s}": base[i, j, q]
                             for q, s in enumerate(("low", "mid", "high"))},
                          "distance_positive": float(vertex_distance(weighted, np.repeat(weights[j], 3))),
                          "distance_negative": float(vertex_distance(weighted, np.zeros(3)))})
    tables["calculation_trace"] = pd.DataFrame(trace)
    correlation_rows = []
    all_central = triangles_from_frame(frame, CRITERIA)[:, :, 1]
    for j, first in enumerate(CRITERIA):
        for k2 in range(j + 1, len(CRITERIA)):
            correlation_rows.append({"first": first, "second": CRITERIA[k2],
                                     "spearman": spearman_scores(all_central[:, j], all_central[:, k2]),
                                     "n": len(ids)})
    tables["criterion_correlations"] = pd.DataFrame(correlation_rows)
    for name, table in tables.items():
        table.to_csv(outdir / f"{prefix}{name}.csv", index=False)
    label = "Hypothetical example" if prefix.startswith("hypothetical") else "Field observations"
    write_sensitivity_figure(summary, outdir / f"{prefix}weight_sensitivity.svg",
                             f"{label}: top-ranked intervention under weight variation")
    return tables

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="completed collated field CSV")
    parser.add_argument("--demo", action="store_true", help="run labelled synthetic example")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--draws", type=int, default=1000)
    args = parser.parse_args()
    if args.demo == bool(args.input):
        parser.error("provide exactly one of --demo or --input")
    if args.draws < 1:
        parser.error("--draws must be positive")
    source = ROOT / "data" / "hypothetical_demo.csv" if args.demo else args.input
    original, eligible = load_and_validate(source)
    prefix = "hypothetical_" if args.demo else "field_"
    tables = evaluate(eligible, args.output_dir, prefix=prefix, draws=args.draws)
    log = pd.DataFrame({"alternative_id": original.alternative_id,
                        "feasibility_status": original.feasibility_status,
                        "action": np.where(original.feasibility_status.eq("eligible"), "included", "excluded")})
    log["notes"] = original["notes"].fillna("") if "notes" in original else ""
    log.to_csv(args.output_dir / f"{prefix}preprocessing_log.csv", index=False)
    eligible.to_csv(args.output_dir / f"{prefix}cleaned_decision_matrix.csv", index=False)
    manifest = {"input_file": str(source), "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "evidence_status": "hypothetical" if args.demo else "user_supplied_unverified_field_data",
                "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                "draws": args.draws, "seed": 20261009, "width_factors": [0, .5, 1],
                "eligible_count": len(eligible), "excluded_count": len(original) - len(eligible),
                "tie_policy": "equal minimum rank; ID display order breaks ties for top-k statistics"}
    (args.output_dir / f"{prefix}run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(tables["base_ranking"].to_string(index=False))
    print(f"Wrote {len(tables) + 4} files to {args.output_dir}")

if __name__ == "__main__":
    main()
