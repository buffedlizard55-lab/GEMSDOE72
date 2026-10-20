"""Prepare the cached feature stack from the competition training data.

Reads data/training_features.tif and data/labels.tif, validates that they match
the competition grid (EPSG:32611, 100 m, 3730 x 3292, competition transform),
converts the -3.4028234663852886e+38 nodata sentinel to NaN, and writes a
cached npz feature stack plus the label mask to data/cache/.

This is scaffolding: it only runs once the login-walled DrivenData training
data has been placed in data/ manually (see scripts/README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.submission_writer import GridSpec  # competition grid spec

DATA = REPO_ROOT / "data"
CACHE = DATA / "cache"
SENTINEL = -3.4028234663852886e+38  # training_features.tif nodata


def prepare(features_path: Path = DATA / "training_features.tif",
            labels_path: Path = DATA / "labels.tif") -> None:
    if not features_path.exists():
        raise SystemExit(
            f"missing {features_path}: place the login-walled DrivenData "
            "training_features.tif in data/ first (see scripts/README.md)"
        )
    if not labels_path.exists():
        raise SystemExit(
            f"missing {labels_path}: place labels.tif in data/ first"
        )

    spec = GridSpec.competition_default()

    with rasterio.open(features_path) as src:
        feat = src.read().astype(np.float64)   # (bands, H, W)
        feat_crs = src.crs.to_string() if src.crs else None
        feat_transform = [src.transform.a, src.transform.b, src.transform.c,
                          src.transform.d, src.transform.e, src.transform.f]
        feat_shape = (int(src.height), int(src.width))

    with rasterio.open(labels_path) as src:
        lab = src.read(1).astype(np.float64)   # (H, W)
        lab_shape = (int(src.height), int(src.width))

    # --- grid validation ---
    ok = True
    if feat_shape != spec.shape:
        print(f"FEATURE shape {feat_shape} != {spec.shape}", file=sys.stderr); ok = False
    if lab_shape != spec.shape:
        print(f"LABEL shape {lab_shape} != {spec.shape}", file=sys.stderr); ok = False
    if feat_crs != spec.crs:
        print(f"FEATURE crs {feat_crs} != {spec.crs}", file=sys.stderr); ok = False
    if feat_transform != list(spec.transform):
        print("FEATURE transform != competition grid", file=sys.stderr); ok = False
    if not ok:
        raise SystemExit("training data grid does not match the competition grid")

    # --- nodata sentinel -> NaN (matches the reference solution) ---
    feat[feat < -1e38] = np.nan
    lab_mask = (lab > 0).astype(np.float64)

    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / "feature_stack.npz", features=feat, labels=lab_mask)
    meta = {
        "shape": list(spec.shape),
        "transform": list(spec.transform),
        "crs": spec.crs,
        "n_bands": int(feat.shape[0]),
        "n_positive_label_px": int((lab_mask > 0).sum()),
        "feature_nan_cells": int(np.isnan(feat).sum()),
    }
    import json
    with open(CACHE / "meta.json", "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)

    print(f"wrote {CACHE/'feature_stack.npz'}")
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    prepare()
