"""Submission writer: produces a format-valid GEMS Prize GeoTIFF + audit receipt.

Format requirements (problem page, https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):
  - single band, 32-bit float, values in [0, 1]
  - EPSG:32611 (UTM zone 11N), 100 m resolution
  - same bounds / transform as the training data
  - every cell finite (no NaN / +/-inf), no nodata sentinel tag

The writer clips values to [0, 1], forces finite, writes float32, and emits a
machine-readable audit receipt (sha256, shape, transform, CRS, min/max, counts)
produced by re-opening the file from disk so the receipt always matches the bytes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from rasterio import Affine

from src.metric import R_M

# Competition grid (verified against the format-validated GEMSDOE32 audit receipt
# for the same competition: shape [3730, 3292], transform below).
DEFAULT_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
DEFAULT_SHAPE = (3730, 3292)  # (height, width)
DEFAULT_CRS = "EPSG:32611"
DEFAULT_PIXEL_SIZE = 100.0


@dataclass
class GridSpec:
    height: int
    width: int
    transform: Affine
    crs: str = DEFAULT_CRS
    pixel_size: float = DEFAULT_PIXEL_SIZE

    @property
    def shape(self):
        return (self.height, self.width)

    @classmethod
    def competition_default(cls) -> "GridSpec":
        a, b, c, d, e, f = DEFAULT_TRANSFORM
        return cls(
            height=DEFAULT_SHAPE[0],
            width=DEFAULT_SHAPE[1],
            transform=Affine(a, b, c, d, e, f),
            crs=DEFAULT_CRS,
            pixel_size=DEFAULT_PIXEL_SIZE,
        )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_array(p: np.ndarray, spec: GridSpec) -> np.ndarray:
    """Clamp to [0, 1], force finite, return float32 array matching spec shape."""
    if p.shape != spec.shape:
        raise ValueError(
            f"prediction shape {p.shape} != grid shape {spec.shape}"
        )
    a = np.asarray(p, dtype=np.float64)
    if not np.all(np.isfinite(a)):
        raise ValueError("prediction contains non-finite values")
    a = np.clip(a, 0.0, 1.0).astype(np.float32)
    return a


def write_submission(
    p: np.ndarray,
    path: Path,
    spec: Optional[GridSpec] = None,
    compress: str = "deflate",
) -> dict:
    """Write a format-valid GeoTIFF submission and return the audit receipt.

    The receipt is computed by re-opening the written file from disk.
    """
    if spec is None:
        spec = GridSpec.competition_default()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    a = validate_array(p, spec)

    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": spec.height,
        "width": spec.width,
        "crs": spec.crs,
        "transform": spec.transform,
        "nodata": None,
        "compress": compress,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
    }

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(a, 1)
        dst.update_tags(1, description="GEMS Prize fault probability [0,1]")

    return _audit(path, spec)


def _audit(path: Path, spec: GridSpec) -> dict:
    """Re-open the file from disk and emit the format audit receipt."""
    with rasterio.open(path) as src:
        data = src.read(1).astype(np.float64)
        crs_str = src.crs.to_string() if src.crs is not None else None
        transform = [
            src.transform.a,
            src.transform.b,
            src.transform.c,
            src.transform.d,
            src.transform.e,
            src.transform.f,
        ]
        height = int(src.height)
        width = int(src.width)
        dtype = src.dtypes[0]
        count = int(src.count)
        nodata = src.nodata
        compress = str(src.compression)
        tiled = bool(src.is_tiled)

    finite_mask = np.isfinite(data)
    in_range = (data >= 0.0) & (data <= 1.0) & finite_mask
    positive = data > 0.0

    receipt = {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "crs": crs_str,
        "transform": transform,
        "shape": [height, width],
        "dtype": dtype,
        "count": count,
        "nodata": nodata,
        "nodata_repr": "None" if nodata is None else str(nodata),
        "compress": compress,
        "tiled": tiled,
    }

    receipt["full_grid_pixels"] = int(data.size)
    receipt["full_grid_finite_pixels"] = int(finite_mask.sum())
    receipt["full_grid_nonfinite_pixels"] = int((~finite_mask).sum())

    receipt["in_footprint_finite_pixels"] = int(finite_mask.sum())
    receipt["in_footprint_nan_pixels"] = int((~np.isfinite(data)).sum())
    receipt["in_footprint_min"] = float(np.min(data)) if data.size else None
    receipt["in_footprint_max"] = float(np.max(data)) if data.size else None
    receipt["in_footprint_range_0_1"] = bool(np.all(in_range))
    receipt["zero_outside_0_1"] = int((~in_range).sum())

    receipt["emitted_positive_pixels"] = int(positive.sum())
    receipt["footprint_fraction"] = float(positive.sum() / data.size) if data.size else 0.0
    receipt["all_finite"] = bool(np.all(finite_mask))
    receipt["all_checks_passed"] = bool(
        count == 1
        and dtype == "float32"
        and (height, width) == spec.shape
        and crs_str == spec.crs
        and bool(np.all(finite_mask))
        and bool(np.all(in_range))
        and nodata is None
    )
    return receipt


def write_audit_json(receipt: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")


def write_zip(tif_path: Path, zip_path: Path) -> None:
    """Zip the single GeoTIFF (DrivenData accepts a .zip containing one GeoTIFF)."""
    import zipfile

    tif_path = Path(tif_path)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif_path, arcname=tif_path.name)
