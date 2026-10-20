"""Submission writer for the GEMS Prize Challenge.

Writes a single-band float32 GeoTIFF in the competition format
(EPSG:32611, 100 m, competition bounds, all finite, values in [0, 1], no
nodata tag) and a machine-readable format-receipt (audit.json) produced by
re-opening the written bytes from disk -- the same self-audit pattern used
by GEMSDOE32's downloads.

Submission format (official, verified 2026-10-20):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine

EXPECTED_DTYPE = np.float32
EXPECTED_CRS = "EPSG:32611"
EXPECTED_PIXEL_M = 100.0

# Competition grid specification (from the GEMSDOE32 format audit, which pins
# the official grid: 3292 x 3730 px, EPSG:32611, transform
# [100, 0, 243350, 0, -100, 4508550]). This is the grid every submission must
# match; see docs/sources.md for provenance.
DEFAULT_TRANSFORM = [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
DEFAULT_SHAPE = [3730, 3292]  # [height, width]


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_submission(
    arr: np.ndarray,
    path: Path | str,
    transform: list[float] | None = None,
    shape: list[int] | None = None,
    crs: str = EXPECTED_CRS,
    nodata=None,
    compress: str = "deflate",
) -> dict:
    """Write `arr` as a competition-format GeoTIFF and return the audit dict.

    `arr` is clipped to [0, 1], cast to float32. NaN/inf are replaced with 0
    so the file is all-finite and every value lies in [0, 1] -- this avoids the
    DrivenData validator error "Predicted values must be in range [0, 1]",
    which is also triggered by the -3.4e38 float32 nodata sentinel.
    """
    path = Path(path)
    transform = transform or DEFAULT_TRANSFORM
    shape = shape or DEFAULT_SHAPE
    height, width = int(shape[0]), int(shape[1])

    arr = np.asarray(arr, dtype=np.float64)
    if arr.shape != (height, width):
        raise ValueError(f"arr shape {arr.shape} != expected ({height}, {width})")
    arr = np.where(np.isfinite(arr), arr, 0.0)
    arr = np.clip(arr, 0.0, 1.0).astype(np.float32)

    aff = Affine(transform[0], transform[1], transform[2],
                 transform[3], transform[4], transform[5])

    profile = dict(
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=CRS.from_string(crs),
        transform=aff,
        nodata=nodata,  # None -> no nodata tag (all-finite file)
        compress=compress,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        BIGTIFF="IF_NEEDED",
    )

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)

    audit = audit_file(path, transform=transform, shape=shape, crs=crs)
    return audit


def audit_file(
    path: Path | str,
    transform: list[float] | None = None,
    shape: list[int] | None = None,
    crs: str = EXPECTED_CRS,
) -> dict:
    """Re-open the written file from disk and run the full format check suite."""
    path = Path(path)
    transform = transform or DEFAULT_TRANSFORM
    shape = shape or DEFAULT_SHAPE
    height, width = int(shape[0]), int(shape[1])

    with rasterio.open(path) as src:
        data = src.read(1)
        meta_crs = src.crs
        meta_transform = list(src.transform)
        meta_dtype = src.dtypes[0]
        meta_nodata = src.nodata
        meta_count = src.count
        meta_w, meta_h = src.width, src.height

    finite_mask = np.isfinite(data)
    in_range = (data >= 0.0) & (data <= 1.0)
    positive = data > 0

    checks = {
        "single_band": bool(meta_count == 1),
        "dtype_float32": bool(meta_dtype == "float32"),
        "dimensions_match": bool((meta_h, meta_w) == (height, width)),
        "crs_epsg_32611": bool(meta_crs is not None and meta_crs.to_epsg() == 32611),
        "transform_matches": bool(
            all(abs(a - b) < 1e-9 for a, b in zip(meta_transform, transform))
        ),
        "all_finite": bool(finite_mask.all()),
        "range_0_1": bool(in_range.all()),
        "zero_nan": bool((~np.isnan(data)).all()),
        "zero_inf": bool((~np.isinf(data)).all()),
        "zero_sentinel_outside_range": bool(
            not np.any((data < -1e30) & finite_mask)
        ),
        "nodata_none": meta_nodata is None,
    }
    checks["all_checks_passed"] = bool(all(checks.values()))

    return {
        "path": str(path),
        "size_bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
        "crs": str(meta_crs) if meta_crs is not None else None,
        "transform": meta_transform,
        "shape": [meta_h, meta_w],
        "dtype": meta_dtype,
        "nodata": meta_nodata,
        "emitted_positive_pixels": int(positive.sum()),
        "positive_value_min": float(data[positive].min()) if positive.any() else None,
        "positive_value_max": float(data[positive].max()) if positive.any() else None,
        "footprint_fraction": float(positive.mean()),
        "min": float(data.min()),
        "max": float(data.max()),
        "finite_pixels": int(finite_mask.sum()),
        "total_pixels": int(data.size),
        "checks": checks,
        "all_checks_passed": checks["all_checks_passed"],
    }


def write_audit(path: Path | str, audit: dict) -> Path:
    path = Path(path)
    path.write_text(json.dumps(audit, indent=2))
    return path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def clipped_note(note: str, max_chars: int = 140) -> str:
    note = " ".join(note.split())
    return note if len(note) <= max_chars else note[: max_chars - 1].rstrip() + "…"
