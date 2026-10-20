"""Prepare competition data for training / inference (stub).

The competition data files are login-walled on DrivenData and cannot be
auto-downloaded from this environment (verified redirect to login at
https://www.drivendata.org/competitions/306/competition-doe-gems/data/).
Run `bash scripts/download_competition_data.sh` on an unrestricted machine
with a logged-in DrivenData session into data/, then run this script to
verify placement and grid identity.

Expected data/ layout after preparation:
    data/
      training_features.tif   # multi-band feature stack, EPSG:32611, 100 m
      labels.tif              # fault label raster, same grid
      sample_submission.tif   # format template (grid: 3730 x 3730... see notes)
      existing_faults.tif
      1m_DEM_links.csv

The submission grid pinned in this repo (scripts/submission_writer.py,
DEFAULT_TRANSFORM = [100, 0, 243350, 0, -100, 4508550], shape 3730 x 3730...
corrected to height=3730, width=3292) matches the GEMSDOE32 format audit,
which states dimensions_3730x3292: true, crs_epsg_32611: true, and every
range/format check passed against the official grid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED = {
    "training_features.tif",
    "labels.tif",
    "sample_submission.tif",
    "existing_faults.tif",
    "1m_DEM_links.csv",
}


def main(data_dir: str = "data") -> int:
    data = Path(data_dir)
    missing = [name for name in sorted(EXPECTED) if not (data / name).exists()]
    report = {
        "data_dir": str(data.resolve()),
        "expected_files": sorted(EXPECTED),
        "missing": missing,
        "ready": not missing,
        "note": "Download from https://www.drivendata.org/competitions/306/"
                "competition-doe-gems/data/ requires a logged-in "
                "DrivenData account. See scripts/download_competition_data.sh.",
    }
    print(json.dumps(report, indent=2))
    if missing:
        print(f"NOT READY: {len(missing)} file(s) missing: {missing}", file=sys.stderr)
        return 1
    print("READY: all competition data files present in data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
