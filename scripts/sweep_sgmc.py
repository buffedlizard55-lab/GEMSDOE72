#!/usr/bin/env python3
"""Experiment 1b: H72-1 SGMC-off-catalogue emission with Poisson-disk thinning sweep.

Sweeps min_dist (packing radius) over the off-catalogue SGMC support, dilated
1 px, and evaluates every mask on the spatially-blocked holdout.  Prints a
comparison table; the best mask is saved to .cache/gems_work/ for packaging.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe72 import holdout as H, emission as E  # noqa: E402

DATA = Path(os.environ.get("GEMS_DATA_DIR", str(ROOT / ".cache" / "gems_data")))
WORK = ROOT / ".cache" / "gems_work"
WORK.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ctx = H.load_holdout_context(DATA, hide_frac=0.20)
    foot, labels = ctx.foot, ctx.labels

    from scipy import ndimage as ndi
    support = ndi.binary_dilation(ctx.sgmc_off & foot, iterations=1) & foot & ~labels
    print("sgmc_off dilated-1 off-catalogue px:", int(support.sum()))

    results = []
    for min_dist in (1.5, 2.0, 2.8, 4.0, 6.0):
        mask = E.dot_thin(support, min_dist)
        res = H.evaluate_candidate_holdout(mask, ctx, name=f"H72-1-d{int(min_dist*10):02d}")
        results.append((min_dist, mask, res))
        print(f"min_dist={min_dist:4.1f} emitted={res['emitted_pixels']:6d} "
              f"on_cat={res['on_catalogue_pixels']} "
              f"cat_hidden_mean={res['catalogue_hidden_mean']:.5f} "
              f"drift_corr_mean={res['drift_corrected_holdout_mean']:.5f} "
              f"quads={ {k: round(v, 4) for k, v in res['drift_corrected_per_quadrant'].items()} }")

    results.sort(key=lambda t: -t[2]["drift_corrected_holdout_mean"])
    best_dist, best_mask, best_res = results[0]
    np.save(WORK / "h72-1-sgmc-best-mask.npy", best_mask)
    q = list(best_res["drift_corrected_per_quadrant"].values())
    se = float(np.std(q, ddof=1)) / np.sqrt(len(q)) if len(q) > 1 else 0.0
    print(f"[BEST] min_dist={best_dist} -> {WORK / 'h72-1-sgmc-best-mask.npy'}")
    print(json.dumps({
        "emitted_pixels": best_res["emitted_pixels"],
        "on_catalogue_pixels": best_res["on_catalogue_pixels"],
        "drift_corrected_holdout_mean": best_res["drift_corrected_holdout_mean"],
        "drift_corrected_95ci": [best_res["drift_corrected_holdout_mean"] - 2 * se,
                                 best_res["drift_corrected_holdout_mean"] + 2 * se],
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
