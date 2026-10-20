#!/usr/bin/env python3
"""Independent re-read validation of a GEMSDOE72 submission GeoTIFF.

Prints a JSON receipt and exits 0 iff the file is legal for the DrivenData
portal (this is what produced the "\"Predicted values must be in range [0,
1]\"" rejection when violated):

  * single band, float32, EPSG:32611, 3730 x 3292, 100 m geotransform
    (identical to sample_submission.tif / labels.tif)
  * every pixel inside the 5,167,373-pixel footprint finite and in [0, 1]
  * nothing but 0.0 (zeros mode) or NaN (nan mode) outside the footprint
  * zero emitted pixels on the competition catalogue (labels)
  * sha256 of the published bytes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe72 import grid, submission as S  # noqa: E402

EXPECTED = dict(height=3730, width=3292, crs="EPSG:32611",
                transform=(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0))


def os_env_data():
    import os
    return os.environ.get("GEMS_DATA_DIR", str(ROOT / ".cache" / "gems_data"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geotiff", type=Path)
    ap.add_argument("--template", type=Path,
                    default=Path(os_env_data()) / "sample_submission.tif")
    ap.add_argument("--labels", type=Path,
                    default=Path(os_env_data()) / "labels.tif")
    ap.add_argument("--strict-finite", action="store_true",
                    help="require every one of the 12,279,160 cells finite and in [0, 1]")
    args = ap.parse_args()

    if not args.geotiff.is_file():
        print(f"[FAIL] {args.geotiff} not found", file=sys.stderr)
        return 2
    for p in (args.template, args.labels):
        if not p.is_file():
            print(f"[FATAL] {p} missing: run `bash scripts/download_competition_data.sh` "
                  "and `python scripts/prepare_data.py` first", file=sys.stderr)
            return 2

    with rasterio.open(args.geotiff) as s:
        arr = s.read(1)
        meta_ok = (s.count == 1 and s.dtypes[0] == "float32" and s.height == 3730
                   and s.width == 3292 and str(s.crs) == "EPSG:32611"
                   and tuple(round(float(v), 6) for v in s.transform)[:6]
                   == EXPECTED["transform"])
        nodata = s.nodata

    with rasterio.open(args.template) as s:
        foot = np.isfinite(s.read(1))
    labels = grid.read_labels(args.labels) & foot

    in_foot = arr[foot]
    out_foot = arr[~foot]
    finite_in = int(np.isfinite(in_foot).sum())
    in_range = bool(finite_in == int(foot.sum()) and np.all((in_foot >= 0) & (in_foot <= 1)))
    emitted = int((in_foot > 0.5).sum())
    on_cat = int(((in_foot > 0.5) & labels[foot]).sum())

    checks = {
        "single_band_float32_epsg32611_3730x3292": bool(meta_ok),
        "in_footprint_all_finite": bool(finite_in == int(foot.sum())),
        "in_footprint_range_0_1": in_range,
        "outside_footprint_zeros_or_nan": bool(np.all(np.isnan(out_foot))
                                               or np.all(out_foot == 0)),
        "zero_on_catalogue_pixels": bool(on_cat == 0),
        "full_grid_finite_and_in_0_1": bool(np.isfinite(arr).all()
                                            and np.all((arr >= 0) & (arr <= 1))),
    }
    passed = all(checks.values())
    receipt = {
        "file": str(args.geotiff),
        "sha256": sha256_file(args.geotiff),
        "bytes": args.geotiff.stat().st_size,
        "crs": "EPSG:32611",
        "transform": list(EXPECTED["transform"]),
        "shape": [3730, 3292],
        "dtype": "float32",
        "nodata": nodata,
        "footprint_px": int(foot.sum()),
        "emitted_pixels": emitted,
        "on_catalogue_pixels": on_cat,
        "in_footprint_finite_px": finite_in,
        "min_in_footprint": float(np.nanmin(in_foot)),
        "max_in_footprint": float(np.nanmax(in_foot)),
        "checks": checks,
        "all_checks_passed": bool(passed),
    }
    print(json.dumps(receipt, indent=1))
    if passed:
        print(f"\n[PASSED] {args.geotiff.name} is valid for submission to the DrivenData portal")
        return 0
    print(f"\n[FAILED] {args.geotiff.name} failed: " +
          ", ".join(k for k, v in checks.items() if not v), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
