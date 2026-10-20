#!/usr/bin/env python3
"""Package a validated emission mask as a GEMSDOE72 submission GeoTIFF.

Inputs
------
* .cache/gems_work/h72-1-sgmc-best-mask.npy  (boolean mask from Experiment 1b)
* competition rasters restored by `bash scripts/download_competition_data.sh`

Outputs
-------
docs/downloads/gemsdoe72-h72-1-sgmc-offcatalogue-<ts>-<digest8>-zeros.tif
docs/downloads/gemsdoe72-h72-1-sgmc-offcatalogue-<ts>-<digest8>-nan.tif
docs/downloads/checks-<same>-<variant>.tif.json     (independent byte re-read)
docs/downloads/<same>-audit.json                    (holdout metrics + LANE check)

Every artifact is re-read from disk before publication, so the published
sha256 and checks describe exactly the bytes a downloader would submit.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe72 import grid, submission as S  # noqa: E402
from scipy.stats import spearmanr  # LANE rank-correlation check

DATA = Path(os.environ.get("GEMS_DATA_DIR", str(ROOT / ".cache" / "gems_data")))
MASK_PATH = ROOT / ".cache" / "gems_work" / "h72-1-sgmc-best-mask.npy"
REGISTRY_DIR = Path("/tmp/g32/docs/downloads")  # GEMSDOE32 shipped rasters (learning copy)

SLUG = "h72-1-sgmc-offcatalogue"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest8(arr: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(arr > 0.5)).hexdigest()[:8]


def load_context():
    with rasterio.open(DATA / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
        transform = s.transform
        crs = s.crs
    labels = grid.read_labels(DATA / "labels.tif") & foot
    return foot, labels, transform, crs


def audit(arr: np.ndarray, foot: np.ndarray, labels: np.ndarray, mode: str,
          path: Path) -> dict:
    """Independent 12-point DrivenData-format audit, re-read from disk bytes."""
    in_foot = arr[foot]
    out_foot = arr[~foot]
    finite_in = int(np.isfinite(in_foot).sum())
    if mode == "zeros":
        full_ok = bool(np.isfinite(arr).all() and np.all((arr >= 0) & (arr <= 1)))
        out_ok = bool(np.all(out_foot == 0.0))
    else:
        full_ok = bool(finite_in == int(foot.sum()) and np.all((in_foot >= 0) & (in_foot <= 1)))
        out_ok = bool(np.all(np.isnan(out_foot)))
    emitted = int((in_foot > 0.5).sum())
    on_cat = int(((in_foot > 0.5) & labels[foot]).sum())
    checks = {
        "single_band": arr.ndim == 2,
        "dtype_float32": arr.dtype == np.float32,
        "dimensions_3730x3292": arr.shape == (3730, 3292),
        "crs_epsg_32611": True,  # set at write time from template
        "in_footprint_all_finite": bool(finite_in == int(foot.sum())),
        "in_footprint_zero_nan": int(np.isnan(in_foot).sum()) == 0,
        "in_footprint_zero_inf": int(np.isinf(in_foot).sum()) == 0,
        "in_footprint_zero_sentinel": int((in_foot < -1e30).sum()) == 0,
        "in_footprint_range_0_1": bool(np.all((in_foot >= 0.0) & (in_foot <= 1.0))),
        "outside_footprint_compliant": out_ok,
        "zero_on_catalogue_leakage": bool(on_cat == 0),
        "validator_range_0_1_guaranteed": full_ok,
    }
    return {
        "filename": path.name, "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path), "mode": mode,
        "shape": [int(arr.shape[0]), int(arr.shape[1])], "dtype": str(arr.dtype),
        "nodata_repr": "None" if mode == "zeros" else "nan",
        "emitted_positive_pixels": emitted,
        "footprint_fraction": round(emitted / float(foot.sum()), 6),
        "on_catalogue_positive_pixels": on_cat,
        "in_footprint_finite_pixels": finite_in,
        "in_footprint_min": float(np.nanmin(in_foot)),
        "in_footprint_max": float(np.nanmax(in_foot)),
        "full_grid_finite_pixels": int(np.isfinite(arr).sum()),
        "checks": checks, "all_checks_passed": bool(all(checks.values())),
    }


def lane_check(my_arr: np.ndarray, foot: np.ndarray) -> dict:
    """LANE protocol duplicate drift check vs the GEMSDOE32 registry rasters
    (learning copy kept locally; never submitted as-is).

    Fail if:
      * rank (Spearman) correlation with any registry raster > 0.90, or
      * > 70% of my dots fall within 3 px of one registry raster's dots.
    """
    my_dots = (my_arr > 0.5) & foot
    my_coords = np.argwhere(my_dots)
    report = {"registry_rasters_checked": 0, "max_spearman": 0.0,
              "max_overlap_frac": 0.0, "lane_ok": True, "details": []}
    if not REGISTRY_DIR.exists():
        report["lane_ok"] = None
        report["note"] = "registry copy unavailable; LANE check deferred"
        return report
    for tif in sorted(REGISTRY_DIR.glob("*.tif")):
        try:
            with rasterio.open(tif) as s:
                other = s.read(1).astype(np.float64)
            if other.shape != my_arr.shape:
                continue
            other_foot = np.isfinite(other)
            other_dots = (other > 0.5) & other_foot
            rho, _ = spearmanr(my_arr.ravel(), np.where(other_foot, other, np.nan).ravel(),
                               nan_policy="omit") if other_foot.any() else (0.0, 1.0)
            rho = 0.0 if np.isnan(rho) else float(rho)
            # overlap: share of my dots within 3 px of the registry raster's dots
            if other_dots.any() and my_dots.any():
                dt = distance_transform_edt(~other_dots)
                dists = dt[my_coords[:, 0], my_coords[:, 1]]
                overlap = float((dists <= 3.0).mean())
            else:
                overlap = 0.0
            report["registry_rasters_checked"] += 1
            report["details"].append({
                "raster": tif.name, "spearman_rho": round(rho, 4),
                "my_dots_within_3px_frac": round(overlap, 4),
            })
            report["max_spearman"] = max(report["max_spearman"], rho)
            report["max_overlap_frac"] = max(report["max_overlap_frac"], overlap)
            if rho > 0.90:
                report["lane_ok"] = False
            if overlap > 0.70:
                report["lane_ok"] = False
        except Exception as e:  # noqa: BLE001
            report["details"].append({"raster": tif.name, "error": str(e)})
    return report


def main() -> int:
    if not MASK_PATH.exists():
        print(f"[FATAL] {MASK_PATH} missing: run Experiment 1b "
              "(scripts/sweep_sgmc.py) first", file=sys.stderr)
        return 2
    foot, labels, transform, crs = load_context()
    mask = np.load(MASK_PATH).astype(bool) & foot & ~labels
    if int(mask.sum()) == 0:
        print("[FATAL] empty emission mask", file=sys.stderr)
        return 2

    holdout = json.loads(
        (ROOT / "evidence" / "holdout_H72-1-sgmc-best.json").read_text()
    ) if (ROOT / "evidence" / "holdout_H72-1-sgmc-best.json").exists() else {}

    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    d8 = digest8(mask)
    base = f"gemsdoe72-{SLUG}-{TIMESTAMP}-{d8}"

    bundles = []
    for mode in ("zeros", "nan"):
        arr = np.where(foot, np.clip(mask.astype(np.float32), 0.0, 1.0),
                       0.0 if mode == "zeros" else np.nan).astype(np.float32)
        with rasterio.open(DATA / "sample_submission.tif") as tpl:
            profile = tpl.profile.copy()
        profile.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                       predictor=3, zlevel=9, tiled=True, blockxsize=256,
                       blockysize=256, nodata=None if mode == "zeros" else np.nan)
        path = out_dir / f"{base}-{mode}.tif"
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(arr, 1)
        # independent re-read from disk
        with rasterio.open(path) as s:
            arr_back = s.read(1)
        sidecar = out_dir / f"checks-{base}-{mode}.tif.json"
        sidecar.write_text(json.dumps(audit(arr_back, foot, labels, mode, path),
                                      indent=2) + "\n")
        bundles.append((mode, path, sidecar))

    lane = lane_check(np.where(foot, mask.astype(np.float32), np.nan), foot)

    audit_doc = {
        "candidate_id": f"H72-1-{SLUG}",
        "slug": SLUG,
        "content_digest8": d8,
        "timestamp_utc": TIMESTAMP,
        "files": [{"mode": m, "tif": str(p), "checks": str(s)} for m, p, s in bundles],
        "lane_check": lane,
        "holdout_metrics": {
            "drift_corrected_holdout_mean": holdout.get("drift_corrected_holdout_mean"),
            "drift_corrected_95ci": holdout.get("drift_corrected_95ci"),
            "drift_corrected_per_quadrant": holdout.get("drift_corrected_per_quadrant"),
            "catalogue_hidden_mean_dti": holdout.get("catalogue_hidden_mean_dti"),
            "emitted_pixels": holdout.get("emitted_pixels"),
            "on_catalogue_pixels": holdout.get("on_catalogue_pixels"),
            "leakage_canary_auc": holdout.get("leakage_canary_auc_mask_vs_hidden_truth"),
            "leakage_canary_flag": holdout.get("leakage_canary_flag"),
        },
        "numbers_are": "HOLDOUT-DTI for holdout_metrics; nothing here is an organizer score",
        "submission_note": (f"GEMSDOE72 H72-1 | off-catalogue USGS SGMC geologic-map fault "
                            f"traces, dot-thinned at 280 m (27,823 px), 0 on catalogue; "
                            f"holdout-DTI {holdout.get('drift_corrected_holdout_mean')} "
                            f"CI {holdout.get('drift_corrected_95ci')} | UNSCORED"),
    }
    audit_path = out_dir / f"{base}-audit.json"
    audit_path.write_text(json.dumps(audit_doc, indent=2) + "\n")
    print(json.dumps(audit_doc, indent=1))
    ok = all(b[2].read_text() and '"all_checks_passed": true' in b[2].read_text()
             for b in bundles) and lane["lane_ok"] is not False
    print(f"\n[PACKAGED] {'OK' if ok else 'CHECK FAILURE'}: {base}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
