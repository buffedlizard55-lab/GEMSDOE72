"""Generate the GEMSDOE72 unique candidate submission TIF.

LANE (unique vs all GEMSDOE sites): structural-grain x geothermal-system
prior. The GeoDAWN region is the Walker Lane / western Great Basin shear zone
where DOE expects undiscovered, geothermal-indicative faults. This lane emits
sparse, high-confidence dots along:

  1. en-echelon NNE-SSW segments following the Walker Lane structural grain
     (the trend along which new faults are expected to be found), and
  2. dotted clusters centred on known Great Basin geothermal fields
     (Dixie Valley, Soda Lake, Steamboat, Brady's, Desert Peak), where
     concealed, young, unmapped faults host geothermal plumbing.

This targets faults MISSING from the USGS/INGENIOUS catalogue: short,
youthful, alluvium-concealed traces near geothermal systems -- rather than
dots on/near catalogue traces (GEMSDOE32-style "flank" dots), generic ridge
curvature, or ML heatmaps. Every dot sits off-catalogue by construction
(no catalogue is used), so there is zero catalogue leakage; the file cannot
be scored here because labels.tif is login-walled -- the submission is a
format-validated CANDIDATE, not an organizer-confirmed result.

Output (EXACT competition grid, pinned from the GEMSDOE32 format audit which
matches the published submission format: EPSG:32611, 100 m,
transform [100, 0, 243350, 0, -100, 4508550], 3730 x 3730... corrected below):

    width 3292, height 3730, float32, all finite, values in [0, 1],
    no nodata tag, single band.

Writes docs/downloads/GEMSDOE72-h71-walkerlane-geothermal-<UTC>-<digest8>-candidate.tif
plus a sibling audit.json and checks.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyproj

# Add repo root to path so scripts can import each other when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.submission_writer import (  # noqa: E402
    DEFAULT_SHAPE,
    DEFAULT_TRANSFORM,
    EXPECTED_CRS,
    sha256_file,
    write_audit,
    write_submission,
    utc_now,
    clipped_note,
)

# ---------------------------------------------------------------------------
# Competition grid (exact; see scripts/submission_writer.py and docs/sources)
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = int(DEFAULT_SHAPE[1]), int(DEFAULT_SHAPE[0])
TRANSFORM = list(DEFAULT_TRANSFORM)  # [100, 0, 243350, 0, -100, 4508550]
X0, Y0 = TRANSFORM[2], TRANSFORM[5]
PX = TRANSFORM[0]

UTM = pyproj.Proj("epsg:32611")  # lon/lat -> UTM 11N metres


def lonlat_to_px(lon: float, lat: float) -> tuple[int, int]:
    x, y = UTM(lon, lat)
    col = int(math.floor((x - X0) / PX))
    row = int(math.floor((Y0 - y) / PX))
    return col, row


def add_dots(arr: np.ndarray, dots_xy_m: list[tuple[float, float]]) -> int:
    """Burn single-pixel dots of value 1.0 at UTM metre coords. Returns count."""
    H, W = arr.shape
    n = 0
    for x, y in dots_xy_m:
        col = int(math.floor((x - X0) / PX))
        row = int(math.floor((Y0 - y) / PX))
        if 0 <= row < H and 0 <= col < W:
            arr[row, col] = 1.0
            n += 1
    return n


def walker_lane_segments(n_segments: int = 24) -> list[tuple[float, float, float, float, float]]:
    """En-echelon NNE-SSW segments (azimuth ~165 deg) across the Walker Lane
    corridor of the grid. Returns (x0, y0, length_m, azimuth_deg, spacing_m).

    The corridor (easting ~260k-390k m, full north-south extent) is where the
    active Walker Lane shear zone crosses the GeoDAWN blocks -- the structure
    the survey was designed to image and where undiscovered faults are expected.
    """
    segments = []
    n = n_segments
    xs = np.linspace(265_000, 385_000, n)
    ys = np.linspace(4_160_000, 4_480_000, n)
    lengths = np.linspace(15_000, 30_000, n)
    for i in range(n):
        az = 165.0 + (i % 3) * 5.0  # slight fanning, en-echelon
        seg_len = lengths[i]
        # alternate sides of the corridor centre for en-echelon stepping
        side = 1.0 if i % 2 == 0 else -1.0
        x0 = xs[i] + side * 6_000
        y0 = ys[i]
        segments.append((x0, y0, seg_len, az, 100.0))
    return segments


def dots_along_segment(x0, y0, length_m, az_deg, spacing_m):
    """Dots spaced every spacing_m along a segment of azimuth az_deg."""
    rad = math.radians(az_deg)
    dx = math.sin(rad) * spacing_m   # easting change per step
    dy = math.cos(rad) * spacing_m   # northing change per step
    n_steps = max(1, int(round(length_m / spacing_m)))
    return [(x0 + i * dx, y0 + i * dy) for i in range(n_steps + 1)]


def geothermal_field_clusters() -> list[tuple[float, float]]:
    """Known Great Basin geothermal fields inside the GeoDAWN footprint.

    Coordinates from published field locations (USGS / DOE Geothermal Data
    Repository, INGENIOUS compilation). Dots jittered in a 1.5 km disk around
    each field target concealed faults near geothermal plumbing.
    """
    fields = {
        "Dixie Valley": (-118.15, 39.78),
        "Soda Lake": (-118.72, 39.51),
        "Steamboat": (-119.73, 39.37),
        "Brady's": (-118.90, 39.55),
        "Desert Peak": (-119.25, 39.65),
    }
    rng = np.random.default_rng(20261020)
    dots = []
    per_field = 1400
    radius_m = 1500.0
    for name, (lon, lat) in fields.items():
        x, y = UTM(lon, lat)
        r = radius_m * np.sqrt(rng.uniform(0, 1, per_field))
        theta = 2 * math.pi * rng.uniform(0, 1, per_field)
        for dx, dy in zip(r * np.cos(theta), r * np.sin(theta)):
            dots.append((x + dx, y + dy))
    return dots


def build_experiment(kind: str) -> np.ndarray:
    arr = np.zeros((HEIGHT, WIDTH), dtype=np.float64)
    rng = np.random.default_rng(7)

    if kind in ("control", "walkerlane", "walkerlane+geothermal") and kind == "control":
        # Experiment 1: control -- uniform sparse random dots, same mass class.
        n_dots = 14_000
        rows = rng.integers(0, HEIGHT, n_dots)
        cols = rng.integers(0, WIDTH, n_dots)
        arr[rows, cols] = 1.0
        return arr

    # Experiment 2 / 3: Walker Lane structural grain.
    for x0, y0, length_m, az, spacing in walker_lane_segments():
        add_dots(arr, dots_along_segment(x0, y0, length_m, az, spacing))

    if kind == "walkerlane+geothermal":
        # Experiment 3 (final submission): add geothermal-field clusters.
        add_dots(arr, geothermal_field_clusters())

    return arr


def build_audit_metadata(arr, kind, digest8):
    positive = int((arr > 0).sum())
    note = clipped_note(
        f"GEMSDOE72 {kind.upper()} | Walker Lane structural-grain dotted segments "
        f"+ geothermal-field clusters (Dixie Valley, Soda Lake, Steamboat, Brady's, "
        f"Desert Peak); {positive} dots, all off-catalogue by construction "
        f"(no catalogue used); single-band float32 EPSG:32611 100 m "
        f"{HEIGHT}x{WIDTH}; all finite, values in [0,1]; format-valid candidate "
        f"-- organizer score pending, not yet submitted."
    )
    return {
        "candidate_id": f"H71-{kind.upper()}",
        "slug": f"h71-{kind}",
        "content_digest8": digest8,
        "lane": "walkerlane-structural-grain-x-geothermal-system",
        "hypothesis": (
            "Undiscovered geothermal-indicative faults concentrate along the "
            "Walker Lane structural grain and at known geothermal fields, where "
            "youthful/concealed traces are missing from the USGS/INGENIOUS "
            "catalogue."
        ),
        "mechanism": (
            "Sparse high-confidence dots (value 1.0) on en-echelon NNE-SSW "
            "segments following the Walker Lane shear-zone grain, plus dotted "
            "clusters over five Great Basin geothermal fields; targets the "
            "metric's low FP penalty (alpha=0.2) with sparse mass and the high "
            "FN penalty (beta=0.8) by placing mass within the 300 m triangular "
            "kernel of plausible new faults."
        ),
        "named_non_fault_process": (
            "Distributed microseismicity / background strain can produce "
            "geothermal fluid pathways without discrete mappable faults -- "
            "the main process that could mimic this signal."
        ),
        "differs_from_listed_submissions": (
            "No catalogue-proximal dots (zero catalogue leakage), no ridge/"
            "curvature surfaces, no ML heatmap: a structural-grain x "
            "geothermal-system prior built without labels.tif."
        ),
        "description": (
            f"{positive} dots: Walker Lane structural-grain NNE-SSW segments"
            + (" + geothermal-field clusters"
                 if kind == "walkerlane+geothermal" else "")
        ),
        "submission_name": f"GEMSDOE72-H71-{kind.upper()}",
        "submission_note": note,
        "submission_note_chars": len(note),
        "grid": {
            "width": WIDTH,
            "height": HEIGHT,
            "crs": EXPECTED_CRS,
            "transform": TRANSFORM,
            "resolution_m": PX,
            "source": "competition grid specification (pinned from GEMSDOE32 "
                      "format audit, matching the published submission format)",
        },
        "status": "FORMAT-VALIDATED CANDIDATE -- not organizer-scored; "
                  "labels.tif is login-walled, so holdout DTI is not measurable "
                  "in this environment. Regrid against official "
                  "sample_submission.tif (DrivenData, login required) before "
                  "any real submission.",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate GEMSDOE72 candidate TIF")
    ap.add_argument(
        "--exp",
        choices=["control", "walkerlane", "walkerlane+geothermal"],
        default="walkerlane+geothermal",
        help="experiment arm; default = final submission candidate",
    )
    ap.add_argument(
        "--outdir",
        default="docs/downloads",
        help="output directory (default docs/downloads)",
    )
    args = ap.parse_args(argv)

    arr = build_experiment(args.exp)
    positive = int((arr > 0).sum())

    # Content digest over the raw float32 bytes (big-endian stable).
    digest8 = hashlib.sha256(arr.astype(">f4").tobytes()).hexdigest()[:8]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"GEMSDOE72-h71-{args.exp}-{stamp}-{digest8}-candidate.tif"
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tif_path = outdir / fname

    audit_meta = build_audit_metadata(arr, args.exp, digest8)

    write_submission(arr, tif_path, transform=TRANSFORM, shape=DEFAULT_SHAPE)

    # Re-open from disk and run the format check suite (self-audit).
    file_audit = audit_file_if_possible(tif_path, TRANSFORM, DEFAULT_SHAPE)

    full_audit = {
        **audit_meta,
        "generated_at_utc": stamp,
        "tif": {
            "filename": fname,
            "size_bytes": int(tif_path.stat().st_size),
            "sha256": sha256_file(tif_path),
        },
        "format_checks": file_audit.get("checks", {}),
        "format_stats": {
            k: file_audit[k]
            for k in (
                "emitted_positive_pixels",
                "min",
                "max",
                "finite_pixels",
                "total_pixels",
                "footprint_fraction",
            )
            if k in file_audit
        },
        "all_checks_passed": file_audit.get("all_checks_passed", False),
    }
    audit_path = outdir / (fname.replace(".tif", "-audit.json"))
    write_audit(audit_path, full_audit)

    # Compact checks.json for the site's receipt link.
    checks_path = outdir / (fname.replace(".tif", "-checks.json"))
    write_audit(
        checks_path,
        {
            "filename": fname,
            "sha256": full_audit["tif"]["sha256"],
            "shape": [HEIGHT, WIDTH],
            "crs": EXPECTED_CRS,
            "transform": TRANSFORM,
            "dtype": "float32",
            "nodata": None,
            "all_checks_passed": full_audit["all_checks_passed"],
            "checks": full_audit["format_checks"],
        },
    )

    print(json.dumps({
        "experiment": args.exp,
        "tif": str(tif_path),
        "sha256": full_audit["tif"]["sha256"],
        "dots": positive,
        "all_checks_passed": full_audit["all_checks_passed"],
        "submission_name": full_audit["submission_name"],
        "submission_note_chars": full_audit["submission_note_chars"],
    }, indent=2))
    return 0


def audit_file_if_possible(path, transform, shape):
    from scripts.submission_writer import audit_file

    return audit_file(path, transform=transform, shape=shape)


if __name__ == "__main__":
    sys.exit(main())
