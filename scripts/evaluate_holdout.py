"""Exact re-implementation of the GEMS distance-weighted Tversky index (DTI).

Source (official problem description, verified 2026-10-20):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

DTI(alpha, beta) = TP_w / (TP_w + alpha * FP_w + beta * FN_w + eps)

with alpha = 0.2 (false-positive penalty), beta = 0.8 (false-negative penalty)
and a triangular kernel k(d) = max(1 - d/R, 0) with range R = 300 m.
At the competition's 100 m resolution, R = 3 px. Distances d are Euclidean
distances between pixel centres in pixels.

    TP_w = sum_{g in G}  max_{x: d(x,g)<=R}  p(x) * k(d(x, g))
    FP_w = sum_{x: p(x)>0}  p(x) * (1 - max_g k(d(x, g)))
    FN_w = sum_{g in G}  (1 - max_{x: d(x,g)<=R} p(x) * k(d(x, g)))

Note FN_w = |G| - TP_w because the inner max lies in [0, 1].

All numbers produced by this module are HOLDOUT-DTI numbers (evaluator version,
spatially-blocked holdout, alpha=0.2, beta=0.8, R=300 m triangular kernel) and
are never organizer-confirmed scores.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ALPHA = 0.2
BETA = 0.8
R_M = 300.0
PIXEL_SIZE_M = 100.0
EPS = 1e-12


def distance_weighted_tversky(
    p: np.ndarray,
    gt: np.ndarray,
    alpha: float = ALPHA,
    beta: float = BETA,
    pixel_size_m: float = PIXEL_SIZE_M,
    R_m: float = R_M,
) -> dict:
    """Distance-weighted Tversky index for probability raster p vs binary gt.

    p : (H, W) float32, values in [0, 1], all finite.
    gt: (H, W) {0, 1}, 1 = ground-truth fault pixel.
    Returns a dict with TP_w, FP_w, FN_w, DTI, n_gt, n_pred.
    """
    p = np.asarray(p, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.float64)
    if p.shape != gt.shape:
        raise ValueError(f"shape mismatch: p {p.shape} vs gt {gt.shape}")
    if not np.all(np.isfinite(p)):
        raise ValueError("p contains non-finite values")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("p contains values outside [0, 1]")

    gt_mask = gt > 0
    n_gt = int(gt_mask.sum())
    n_pred = int((p > 0).sum())

    if n_gt == 0:
        return {
            "TP_w": 0.0,
            "FP_w": float(p.sum()),
            "FN_w": 0.0,
            "DTI": 0.0,
            "n_gt": 0,
            "n_pred": n_pred,
            "note": "empty ground truth",
        }

    R_px = R_m / pixel_size_m
    H, W = p.shape

    # ---- FP_w: distance from every cell to the nearest GT pixel ----------
    # dist[x] = distance to nearest GT pixel (px). w(x) = max_g k(d(x,g))
    #         = max(1 - dist[x]/R_px, 0)  (the nearest GT gives the largest k)
    dist = ndimage.distance_transform_edt(~gt_mask)  # inf where no GT at all
    dist = np.where(np.isfinite(dist), dist, R_px + 1.0)
    w = np.clip(1.0 - dist / R_px, 0.0, 1.0)
    fp_w = float((p * (1.0 - w)).sum())

    # ---- TP_w / FN_w: for every GT pixel, best prediction within R -------
    tp_w = 0.0
    half = int(math.ceil(R_px))
    ys, xs = np.nonzero(gt_mask)
    for gy, gx in zip(ys.tolist(), xs.tolist()):
        r0, r1 = max(0, gy - half), min(H, gy + half + 1)
        c0, c1 = max(0, gx - half), min(W, gx + half + 1)
        nb = p[r0:r1, c0:c1]
        if nb.size == 0:
            continue
        yy, xx = np.nonzero(nb)
        dy = (yy + r0) - gy
        dx = (xx + c0) - gx
        d = np.hypot(dy, dx)
        k = np.clip(1.0 - d / R_px, 0.0, 1.0)
        best = float((nb[yy, xx] * k).max()) if nb[yy, xx].size else 0.0
        tp_w += best

    fn_w = float(n_gt - tp_w)
    dti = tp_w / (tp_w + alpha * fp_w + beta * fn_w + EPS)

    return {
        "TP_w": float(tp_w),
        "FP_w": fp_w,
        "FN_w": fn_w,
        "DTI": float(dti),
        "n_gt": n_gt,
        "n_pred": n_pred,
    }


def holdout_folds_from_segments(
    gt: np.ndarray,
    segment_buffer_px: int = 6,
    n_folds: int = 4,
) -> list[np.ndarray]:
    """Spatially-blocked holdout: withhold whole fault segments.

    Connected components of the gt mask are fault segments. Segments are
    assigned to folds by the angle of their principal axis (4 directional
    blocks) so no fold shares segment orientation with another, then each
    fold's test mask = pixels within `segment_buffer_px` of its withheld
    segments. Train = all other pixels. Visible faults are masked pixel-exactly
    before feature derivation (caller applies the mask to features).

    Returns a list of (train_mask, test_mask) boolean arrays, one per fold.
    """
    gt = np.asarray(gt, dtype=np.float64)
    gt_mask = gt > 0
    labeled, n_seg = ndimage.label(gt_mask)
    if n_seg == 0:
        return []

    # Orientation of each segment (principal axis via covariance of coords).
    slices = ndimage.find_objects(labeled)
    angles = []
    for sl in slices:
        yy, xx = np.nonzero(labeled[sl] == (slices.index(sl) + 1))
        if len(yy) < 3:
            angles.append(0.0)
            continue
        yy = yy.astype(np.float64) + sl[0].start
        xx = xx.astype(np.float64) + sl[1].start
        c = np.cov(yy, xx)
        # principal axis angle of the *line* (undirected, in [0, pi))
        ang = 0.5 * math.atan2(2 * c[0, 1], c[0, 0] - c[1, 1])
        angles.append(ang % math.pi)

    order = np.argsort(angles)
    folds = np.array_split(order, n_folds)  # segment indices per fold

    masks = []
    for fold_seg_idxs in folds:
        test = np.zeros_like(gt_mask, dtype=bool)
        for si in fold_seg_idxs:
            seg = labeled == (si + 1)
            dilated = ndimage.binary_dilation(
                seg, iterations=segment_buffer_px
            )
            test |= dilated
        train = ~test
        masks.append((train, test))
    return masks


def pooled_holdout_dti(
    p: np.ndarray,
    gt: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    alpha: float = ALPHA,
    beta: float = BETA,
    pixel_size_m: float = PIXEL_SIZE_M,
    R_m: float = R_M,
) -> dict:
    """Score pooled DTI across holdout folds (counts pooled before the ratio)."""
    tp_w = fp_w = fn_w = 0.0
    n_gt = n_pred = 0
    per_fold = []
    for fold_idx, (train, test) in enumerate(folds):
        # Features derived only from visible faults: predictions p are already
        # conditioned on visible faults by the caller; here we score the
        # withheld segment buffers only.
        res = distance_weighted_tversky(
            np.where(test, p, 0.0),
            np.where(test, gt, 0.0),
            alpha=alpha,
            beta=beta,
            pixel_size_m=pixel_size_m,
            R_m=R_m,
        )
        tp_w += res["TP_w"]
        fp_w += res["FP_w"]
        fn_w += res["FN_w"]
        n_gt += res["n_gt"]
        n_pred += res["n_pred"]
        per_fold.append(res)
    dti = tp_w / (tp_w + alpha * fp_w + beta * fn_w + EPS)
    return {
        "TP_w": tp_w,
        "FP_w": fp_w,
        "FN_w": fn_w,
        "DTI": float(dti),
        "n_gt": n_gt,
        "n_pred": n_pred,
        "per_fold": per_fold,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate DTI on a holdout set")
    ap.add_argument("--predictions", required=True, help="prediction GeoTIFF")
    ap.add_argument("--labels", required=True, help="ground-truth label GeoTIFF")
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--beta", type=float, default=BETA)
    args = ap.parse_args(argv)

    try:
        import rasterio
    except ImportError as exc:  # pragma: no cover - environment guard
        print(f"ERROR: rasterio required: {exc}", file=sys.stderr)
        return 2

    with rasterio.open(args.predictions) as src:
        p = src.read(1).astype(np.float64)
    with rasterio.open(args.labels) as src:
        gt = src.read(1).astype(np.float64)

    res = distance_weighted_tversky(p, gt, alpha=args.alpha, beta=args.beta)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
