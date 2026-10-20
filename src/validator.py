"""Independent submission format validator.

Re-opens a written GeoTIFF from disk and checks every competition format
requirement.  Intended to be run as the final gate before a file is offered for
download / submission.

Checks
------
- single band, float32
- shape == (3730, 3292), CRS == EPSG:32611
- transform matches the competition grid exactly
- no nodata tag (nodata is None)
- every cell finite (no NaN / +/-inf)  [no NaN inside the footprint]
- all values in [0, 1]
- transform bounds reproduce the competition extent
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from rasterio import Affine

EXPECTED_HEIGHT = 3730
EXPECTED_WIDTH = 3292
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_PIXEL = 100.0
EXPECTED_COUNT = 1
EXPECTED_DTYPE = "float32"


@dataclass
class ValidationResult:
    passed: bool
    checks: dict
    message: str

    @classmethod
    def ok(cls, checks: dict) -> "ValidationResult":
        return cls(passed=True, checks=checks, message="all format checks passed")

    @classmethod
    def fail(cls, checks: dict, message: str) -> "ValidationResult":
        return cls(passed=False, checks=checks, message=message)


def validate(path, expect_transform: Optional[tuple] = None) -> ValidationResult:
    path = Path(path)
    if not path.exists():
        return ValidationResult.fail({}, f"file not found: {path}")

    checks: dict = {}
    failures = []

    with rasterio.open(path) as src:
        checks["driver"] = src.driver
        checks["count"] = int(src.count)
        checks["dtype"] = src.dtypes[0]
        checks["height"] = int(src.height)
        checks["width"] = int(src.width)
        checks["crs"] = src.crs.to_string() if src.crs is not None else None
        checks["transform"] = [
            src.transform.a, src.transform.b, src.transform.c,
            src.transform.d, src.transform.e, src.transform.f,
        ]
        checks["nodata"] = src.nodata
        checks["compress"] = src.compression
        checks["tiled"] = src.is_tiled

        data = src.read(1).astype(np.float64)
        transform = src.transform

    # --- structural checks ---
    checks["single_band"] = checks["count"] == EXPECTED_COUNT
    if checks["single_band"] is not True:
        failures.append(f"expected {EXPECTED_COUNT} band, got {checks['count']}")

    checks["dtype_float32"] = checks["dtype"] == EXPECTED_DTYPE
    if not checks["dtype_float32"]:
        failures.append(f"expected dtype {EXPECTED_DTYPE}, got {checks['dtype']}")

    checks["dimensions"] = (checks["height"], checks["width"]) == (
        EXPECTED_HEIGHT, EXPECTED_WIDTH,
    )
    if not checks["dimensions"]:
        failures.append(
            f"expected shape ({EXPECTED_HEIGHT},{EXPECTED_WIDTH}), "
            f"got ({checks['height']},{checks['width']})"
        )

    checks["crs_epsg_32611"] = checks["crs"] == EXPECTED_CRS
    if not checks["crs_epsg_32611"]:
        failures.append(f"expected CRS {EXPECTED_CRS}, got {checks['crs']}")

    et = expect_transform or EXPECTED_TRANSFORM
    checks["transform_matches"] = all(
        abs(checks["transform"][i] - et[i]) < 1e-6 for i in range(6)
    )
    if not checks["transform_matches"]:
        failures.append(f"transform mismatch: {checks['transform']} vs {et}")

    checks["nodata_none"] = checks["nodata"] is None
    if not checks["nodata_none"]:
        failures.append(f"expected no nodata tag, got {checks['nodata']}")

    # --- value checks ---
    finite_mask = np.isfinite(data)
    checks["all_finite"] = bool(np.all(finite_mask))
    if not checks["all_finite"]:
        failures.append(f"{int((~finite_mask).sum())} non-finite cells")

    checks["no_nan"] = bool(np.all(~np.isnan(data)))
    checks["no_inf"] = bool(np.all(~np.isinf(data)))

    in_range = (data >= 0.0) & (data <= 1.0) & finite_mask
    checks["range_0_1"] = bool(np.all(in_range))
    if not checks["range_0_1"]:
        failures.append(
            f"{int((~in_range).sum())} cells outside [0, 1] or non-finite"
        )

    checks["min"] = float(np.min(data)) if data.size else None
    checks["max"] = float(np.max(data)) if data.size else None
    checks["positive_pixels"] = int((data > 0).sum())
    checks["nan_count"] = int(np.isnan(data).sum())

    # --- bounds / extent check ---
    xs = transform * (checks["width"], 0)  # not directly; compute corners manually
    a, b, c, d, e, f = (
        transform.a, transform.b, transform.c,
        transform.d, transform.e, transform.f,
    )
    x_min = c
    x_max = c + checks["width"] * a + checks["height"] * b
    y_max = f
    y_min = f + checks["height"] * e
    checks["bounds"] = [x_min, y_min, x_max, y_max]
    expected_x_max = EXPECTED_TRANSFORM[2] + EXPECTED_WIDTH * EXPECTED_PIXEL
    expected_y_min = EXPECTED_TRANSFORM[5] - EXPECTED_HEIGHT * EXPECTED_PIXEL
    checks["extent_matches"] = (
        abs(x_min - EXPECTED_TRANSFORM[2]) < 1e-6
        and abs(x_max - expected_x_max) < 1e-6
        and abs(y_max - EXPECTED_TRANSFORM[5]) < 1e-6
        and abs(y_min - expected_y_min) < 1e-6
    )
    if not checks["extent_matches"]:
        failures.append("bounds/extent do not match the competition grid")

    passed = len(failures) == 0
    message = "all format checks passed" if passed else "; ".join(failures)
    return ValidationResult(passed=passed, checks=checks, message=message)


def validate_file(path) -> ValidationResult:
    return validate(path)
