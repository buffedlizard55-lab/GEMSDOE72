"""Distance-weighted Tversky index (DTI) for the DOE GEMS Prize Challenge.

Implements the metric verbatim from the competition problem page:
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

    alpha = 0.2  (penalty on false positives)
    beta  = 0.8  (penalty on false negatives)
    R     = 300 m = 3 px at 100 m resolution (triangular kernel support)

    k(d) = max(1 - d/R, 0)

    TPw = sum_{g in G} max_{x: d(x,g)<=R} p(x) * k(d(x,g))
    FPw = sum_{x: p(x)>0} p(x) * [1 - max_{g in G} k(d(x,g))]
    FNw = sum_{g in G} [1 - max_{x: d(x,g)<=R} p(x) * k(d(x,g))]

    DTI = TPw / (TPw + alpha*FPw + beta*FNw + eps)

The worked example on the problem page reports TPw=3.00, FPw=1.89, FNw=2.00
-> DTI = 3.00 / (3.00 + 0.2*1.89 + 0.8*2.00) = 0.6026... ~= 0.60.
tests/test_metric.py reproduces this on a small hand-computable grid.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

ALPHA = 0.2
BETA = 0.8
R_M = 300.0          # kernel support, metres
EPS = 1e-12          # denominator stabiliser


def triangular_kernel(d: np.ndarray, R: float = R_M) -> np.ndarray:
    """Triangular (linear) kernel k(d) = max(1 - d/R, 0)."""
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / float(R), 0.0)


def _pixel_coords(shape, pixel_size: float = 100.0):
    """Return (N,2) float64 array of pixel centres in metres (y, x)."""
    h, w = shape
    ys, xs = np.mgrid[0:h, 0:w]
    return np.column_stack([ys.ravel() * pixel_size, xs.ravel() * pixel_size])


def distance_weighted_tversky(
    p: np.ndarray,
    gt: np.ndarray,
    pixel_size: float = 100.0,
    alpha: float = ALPHA,
    beta: float = BETA,
    R: float = R_M,
) -> dict:
    """Compute the distance-weighted Tversky index and its components.

    Parameters
    ----------
    p : (H, W) float, predicted fault probability in [0, 1].
    gt  : (H, W) {0,1}, ground-truth fault mask.
    pixel_size : metres per pixel (100 m for this competition).

    Returns
    -------
    dict with keys DTI, TPw, FPw, FNw, alpha, beta, R, n_pred, n_gt.
    """
    p = np.asarray(p, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.float64)
    if p.shape != gt.shape:
        raise ValueError(f"shape mismatch p={p.shape} gt={gt.shape}")
    if not np.all(np.isfinite(p)):
        raise ValueError("p contains non-finite values")
    if np.any(p < 0.0) or np.any(p > 1.0):
        raise ValueError("p values must lie in [0, 1]")

    h, w = p.shape
    gt_mask = gt > 0.0
    pred_mask = p > 0.0

    n_gt = int(gt_mask.sum())
    n_pred = int(pred_mask.sum())

    # Degenerate cases.
    if n_gt == 0:
        # No ground truth: everything predicted is a false positive at full weight.
        fpw = float(pred_mask.sum() * p[pred_mask].sum()) if n_pred else 0.0
        return {
            "DTI": 0.0 if fpw > 0 else 1.0,
            "TPw": 0.0, "FPw": fpw, "FNw": 0.0,
            "alpha": alpha, "beta": beta, "R": R,
            "n_pred": n_pred, "n_gt": 0,
        }
    if n_pred == 0:
        return {
            "DTI": 0.0,
            "TPw": 0.0, "FPw": 0.0, "FNw": float(n_gt),
            "alpha": alpha, "beta": beta, "R": R,
            "n_pred": 0, "n_gt": n_gt,
        }

    gt_coords = _pixel_coords(p.shape, pixel_size)[gt_mask.ravel()]
    pred_coords = _pixel_coords(p.shape, pixel_size)[pred_mask.ravel()]
    pred_vals = p[pred_mask]

    gt_tree = cKDTree(gt_coords)
    pred_tree = cKDTree(pred_coords)

    # ---- FPw: for each predicted pixel, distance to nearest ground truth ----
    dist_pred_to_gt, _ = gt_tree.query(pred_coords, k=1)  # metres
    k_nearest = triangular_kernel(dist_pred_to_gt, R)     # 0 if beyond R
    fpw = float(np.sum(pred_vals * (1.0 - k_nearest)))

    # ---- TPw / FNw: for each ground truth pixel, best covered prediction ----
    # predicted pixels within R of each ground-truth pixel
    pred_within_R = pred_tree.query_ball_point(gt_coords, r=R)

    tpw = 0.0
    for g_idx, neigh in enumerate(pred_within_R):
        if len(neigh) == 0:
            # uncovered ground truth -> contributes 1 to FNw, 0 to TPw
            continue
        neigh = np.asarray(neigh, dtype=int)
        d = np.linalg.norm(pred_coords[neigh] - gt_coords[g_idx], axis=1)
        cover = np.max(pred_vals[neigh] * triangular_kernel(d, R))
        tpw += float(cover)

    fnw = float(n_gt) - tpw

    dti = tpw / (tpw + alpha * fpw + beta * fnw + EPS)

    return {
        "DTI": float(dti),
        "TPw": float(tpw),
        "FPw": float(fpw),
        "FNw": float(fnw),
        "alpha": float(alpha),
        "beta": float(beta),
        "R": float(R),
        "n_pred": n_pred,
        "n_gt": n_gt,
    }


def dti(p: np.ndarray, gt: np.ndarray, **kwargs) -> float:
    """Convenience: return only the DTI scalar."""
    return distance_weighted_tversky(p, gt, **kwargs)["DTI"]
