#!/usr/bin/env python3
"""GEMSDOE72 holdout-DTI evaluation for one candidate emission mask.

Implements the lane method verbatim:

    Holdout = hide-and-recover: withhold whole fault segments with a buffer,
    derive every catalogue-based feature only from the visible faults, mask
    visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8,
    300 m triangular kernel).

Every number it prints is a HOLDOUT-DTI number (evaluator version, number of
withheld positives, 95% CI across the four spatial quadrants) -- never a
projection of an organizer score.

Usage:
    .venv/bin/python scripts/evaluate_holdout.py --builtin sgmc_off_catalogue --name H72-1
    .venv/bin/python scripts/evaluate_holdout.py --builtin tmi_gradient --budget 8000 --name H72-2
    .venv/bin/python scripts/evaluate_holdout.py --builtin random --budget 8000 --name RANDOM-CTRL
    .venv/bin/python scripts/evaluate_holdout.py --mask /path/to/mask.npy --name CUSTOM
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe72 import holdout as H, metric as M, emission as E, grid  # noqa: E402

DATA = Path(os.environ.get("GEMS_DATA_DIR", str(ROOT / ".cache" / "gems_data")))


def auc_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney U) with average ranks for ties."""
    y_true = np.asarray(y_true).ravel().astype(bool)
    y_score = np.asarray(y_score, dtype=np.float64).ravel()
    pos = y_score[y_true]
    neg = y_score[~y_true]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    order = np.argsort(y_score, kind="mergesort")
    ranks = np.empty(order.size, dtype=np.float64)
    sorted_vals = y_score[order]
    i = 0
    while i < order.size:
        j = i
        while j + 1 < order.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        avg = 0.5 * (i + 1) + 0.5 * (j + 1)
        ranks[order[i:j + 1]] = avg
        i = j + 1
    u = float(ranks[y_true].sum() - pos.size * (pos.size + 1) / 2.0)
    return float(u / (pos.size * neg.size))


def ci95(values: list[float]) -> tuple[float, float, float]:
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean())
    if arr.size > 1:
        se = float(arr.std(ddof=1)) / np.sqrt(arr.size)
        return mean, mean - 2.0 * se, mean + 2.0 * se
    return mean, mean, mean


def mask_sgmc_off_catalogue(ctx: H.HoldoutContext, dilate_px: int = 0) -> np.ndarray:
    """H72-1: USGS SGMC geologic-map fault traces off the competition
    catalogue. Independent of the catalogue by construction; the holdout
    engine masks visible faults pixel-exactly at scoring time."""
    from scipy import ndimage
    m = ctx.sgmc_off & ctx.foot
    if dilate_px:
        m = ndimage.binary_dilation(m, iterations=int(dilate_px))
        m = m & ctx.foot & ~ctx.labels
    return m


def mask_tmi_gradient(ddir: Path, footprint: np.ndarray, budget: int) -> np.ndarray:
    """H72-2: aeromagnetic horizontal-gradient lineaments (band 03 ``tmi_hg``
    of the pinned numerical-features stack), top-k by gradient magnitude
    inside the footprint."""
    with rasterio.open(ddir / "training_features.tif") as s:
        band = s.tags(3).get("band_name", "band_3")
        field = s.read(3).astype(np.float32)
    valid = np.isfinite(field) & footprint
    field = np.where(valid, field, -np.inf)
    return E.topk_mask(field, budget, footprint)


def mask_random(footprint: np.ndarray, budget: int, seed: int = 0) -> np.ndarray:
    """A4 random control: ``budget`` uniform random in-domain pixels."""
    rng = np.random.default_rng(seed)
    flat = np.argwhere(footprint)
    pick = rng.choice(flat.size, size=min(budget, flat.size), replace=False)
    m = np.zeros(footprint.shape, bool)
    m[tuple(flat[pick].T)] = True
    return m


def pooled_auc_mask_vs_hidden(mask: np.ndarray, ctx: H.HoldoutContext) -> float:
    """Leakage canary: rank AUC of the candidate mask against the held-out
    (hidden) truth, pooled over the 8 blocked draws. A catalogue-independent
    layer should be far below 0.90; above 0.90 means leakage until proven
    otherwise."""
    y_true, y_score = [], []
    for cell in ctx.cells:
        sl = cell.bbox
        m_sub = (mask[sl] & cell.active_sub).ravel()
        t_sub = np.zeros(cell.active_sub.shape, bool)
        t_sub[cell.truth_coords] = True
        y_true.append(t_sub.ravel().astype(np.float64))
        y_score.append(m_sub.astype(np.float64))
    return auc_score(np.concatenate(y_true), np.concatenate(y_score))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mask", type=Path, default=None,
                    help="path to a boolean .npy mask (must match the grid)")
    ap.add_argument("--builtin", choices=("sgmc_off_catalogue", "sgmc_off_catalogue_d1",
                                          "tmi_gradient", "random"),
                    default="sgmc_off_catalogue")
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--name", required=True, help="candidate id used in outputs")
    ap.add_argument("--hide-frac", type=float, default=0.20)
    ap.add_argument("--dilate", type=int, default=1)
    ap.add_argument("--out", type=Path, default=None,
                    help="write evidence JSON here (default evidence/holdout_<name>.json)")
    a = ap.parse_args()

    if not DATA.exists():
        print(f"[FATAL] competition data not found at {DATA}. Run "
              "`bash scripts/download_competition_data.sh` first.", file=sys.stderr)
        return 2

    ctx = H.load_holdout_context(DATA, hide_frac=a.hide_frac)
    foot, labels = ctx.foot, ctx.labels

    if a.mask is not None:
        mask = np.load(a.mask).astype(bool) & foot
        builtin = "file"
    elif a.builtin == "sgmc_off_catalogue":
        mask = mask_sgmc_off_catalogue(ctx, dilate_px=0)
        builtin = "sgmc_off_catalogue"
    elif a.builtin == "sgmc_off_catalogue_d1":
        mask = mask_sgmc_off_catalogue(ctx, dilate_px=a.dilate)
        builtin = f"sgmc_off_catalogue_d{a.dilate}"
    elif a.builtin == "tmi_gradient":
        mask = mask_tmi_gradient(DATA, foot, a.budget)
        builtin = "tmi_gradient"
    else:
        mask = mask_random(foot, a.budget)
        builtin = "random"

    mask = mask & ~labels  # pixel-exact catalogue mask (belt and braces)
    res = H.evaluate_candidate_holdout(mask, ctx, name=a.name)

    # Leakage canary: mask vs held-out truth AUC (mask is binary, so it ranks
    # emitted pixels above non-emitted ones).
    canary_auc = pooled_auc_mask_vs_hidden(mask, ctx)

    # 95% CI over the four quadrant means (drift-corrected per-quadrant).
    q = list(res["drift_corrected_per_quadrant"].values())
    mean, lo, hi = ci95(q)

    out = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evaluator": "holdout-DTI (GEMSDOE72 lane; alpha=0.2, beta=0.8, R=300 m = 3 px)",
        "holdout": "hide-and-recover: 8 blocked draws (4 quadrants x draws 20/21), "
                   f"hide_frac={a.hide_frac}, collar=15 px, domain erosion=12 px",
        "candidate": {"name": a.name, "builtin": builtin},
        "data_root": str(DATA),
        "numbers_are": "HOLDOUT-DTI only -- no organizer score is claimed or projected",
        "emitted_pixels": res["emitted_pixels"],
        "share_of_footprint": res["share_of_footprint"],
        "on_catalogue_pixels": res["on_catalogue_pixels"],
        "on_catalogue_waste_frac": res["on_catalogue_waste_frac"],
        "hug_share": res["hug_share"],
        "catalogue_hidden_mean_dti": res["catalogue_hidden_mean"],
        "catalogue_hidden_std": res["catalogue_hidden_std"],
        "catalogue_hidden_per_quadrant": res["catalogue_hidden_per_quadrant"],
        "catalogue_hidden_per_draw": res["catalogue_hidden_per_draw"],
        "drift_corrected_holdout_mean": res["drift_corrected_holdout_mean"],
        "drift_corrected_holdout_std": res["drift_corrected_holdout_std"],
        "drift_corrected_per_quadrant": res["drift_corrected_per_quadrant"],
        "drift_corrected_95ci": [lo, mean, hi],
        "leakage_canary_auc_mask_vs_hidden_truth": canary_auc,
        "leakage_canary_flag": bool(canary_auc > 0.90),
        "sgmc_prevalence_calibrated_dti": res["sgmc_prevalence_calibrated_dti"],
        "catalogue_hidden_folds": res["catalogue_hidden_folds"],
    }
    print(json.dumps(out, indent=1))

    out_path = a.out or (ROOT / "evidence" / f"holdout_{a.name}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"[OK] evidence written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
