"""Priority-oriented triangular fuzzy TOPSIS calculation.

The vertex metric, criterion-distance summation and closeness coefficient follow
Chen (2000). Our observed-range preprocessing and crisp weights are disclosed
adaptations to the crossing-priority problem.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

def validate_weights(weights):
    """Return nonnegative finite weights scaled to sum to one."""
    w = np.asarray(weights, dtype=float)
    if (w.ndim != 1 or w.size == 0 or not np.isfinite(w).all()
            or (w < 0).any() or w.max() <= 0):
        raise ValueError("weights must be finite, nonnegative, and have positive sum")
    w = w / w.max()  # Avoid overflow when summing large but finite weights.
    return w / w.sum()

def normalize_priority(values, directions):
    """Orient a crisp matrix so larger values always mean higher priority."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or x.shape[0] == 0 or not np.isfinite(x).all():
        raise ValueError("expected a nonempty finite 2-D matrix")
    if len(directions) != x.shape[1] or any(d not in {"benefit", "cost"} for d in directions):
        raise ValueError("each criterion needs a benefit or cost direction")
    out = np.zeros_like(x)
    for j, direction in enumerate(directions):
        low, high = x[:, j].min(), x[:, j].max()
        if high == low:
            continue
        if direction == "benefit":
            out[:, j] = (x[:, j] - low) / (high - low)
        else:
            out[:, j] = (high - x[:, j]) / (high - low)
    return out

def vertex_distance(a, b):
    """Chen's vertex distance for triangular fuzzy numbers."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape[-1] != 3 or b.shape[-1] != 3:
        raise ValueError("triangular numbers need three coordinates")
    return np.sqrt(np.mean((a - b) ** 2, axis=-1))

def intervalize(triangles):
    """Normalize priority-oriented TFNs with common outer bounds per criterion.

    Constant columns become zero; fuzzy_topsis removes them before weighting.
    """
    z = np.asarray(triangles, dtype=float).copy()
    if z.ndim != 3 or z.shape[0] < 2 or z.shape[1] < 1 or z.shape[2] != 3:
        raise ValueError("expected at least two alternatives and (n, m, 3) values")
    if not np.isfinite(z).all():
        raise ValueError("triangles must be finite")
    if (z[:, :, 0] > z[:, :, 1]).any() or (z[:, :, 1] > z[:, :, 2]).any():
        raise ValueError("require low <= central <= high")
    for j in range(z.shape[1]):
        low, high = z[:, j, 0].min(), z[:, j, 2].max()
        z[:, j, :] = 0 if high == low else (z[:, j, :] - low) / (high - low)
    return z

def fuzzy_topsis(triangles, weights):
    """Return closeness and distances using summed Chen vertex distances.

    Inputs have shape (alternatives, criteria, 3), values in [0,1], and all
    criteria are oriented so larger is higher priority. Crisp weights are a
    project adaptation. Identical columns are removed and weights renormalized.
    """
    a = np.asarray(triangles, dtype=float)
    w = validate_weights(weights)
    if a.ndim != 3 or a.shape[0] < 2 or a.shape[2] != 3 or a.shape[1] != w.size:
        raise ValueError("bad triangle/weight shape")
    if (not np.isfinite(a).all() or (a < 0).any() or (a > 1).any()
            or (a[:, :, 0] > a[:, :, 1]).any()
            or (a[:, :, 1] > a[:, :, 2]).any()):
        raise ValueError("normalized triangles must be ordered, finite, and in [0,1]")
    active = np.ptp(a, axis=0).max(axis=1) > 1e-12
    if not active.any():
        raise ValueError("no criterion distinguishes the alternatives")
    a, w = a[:, active, :], validate_weights(w[active])
    weighted = a * w[None, :, None]
    positive = np.ones((a.shape[1], 3)) * w[:, None]
    negative = np.zeros((a.shape[1], 3))
    # Chen-style summation is over criterion vertex distances, not their squares.
    d_plus = vertex_distance(weighted, positive[None, :, :]).sum(axis=1)
    d_minus = vertex_distance(weighted, negative[None, :, :]).sum(axis=1)
    denominator = d_plus + d_minus
    if (denominator <= 0).any():
        raise ValueError("undefined closeness: zero distance denominator")
    return d_minus / denominator, d_plus, d_minus

def rank_dataframe(ids, scores, method):
    """Sort by score, then ID for deterministic ordering of exact ties."""
    return (pd.DataFrame({"alternative_id": ids, "score": scores, "method": method})
            .sort_values(["score", "alternative_id"], ascending=[False, True])
            .reset_index(drop=True))
