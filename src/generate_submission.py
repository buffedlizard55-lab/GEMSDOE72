"""Generate a unique GEMS Prize submission GeoTIFF.

This is the submission *packaging* step: it takes a prediction array, writes a
format-valid single-band float32 GeoTIFF on the exact competition grid
(EPSG:32611, 100 m, 3730x3292, transform from the format-validated GEMSDOE32
audit receipt for the same competition), emits a sha256-pinned audit receipt,
and runs the independent validator.

The prediction content here is a *baseline* (a fixed-budget dotted emission),
because the competition training features/labels are login-walled on DrivenData
and cannot be downloaded from this sandbox.  The file is therefore:

  * OK TO SUBMIT (format-valid):  YES  -- passes the validator (CRS/shape/
    transform/range/[0,1]/finite/no-nodata).
  * COMPETITIVE / HIGH-SCORING:    NOT CLAIMED.  Score is unverified; this is a
    baseline, not a leaderboard submission.  To make it competitive, place the
    competition data in data/ and train/validate per scripts/README.

This follows the GEMSDOE32 convention: every number is labelled
HOLDOUT-DTI / ORGANIZER-CONFIRMED / or UNSCORED baseline; nothing is offered
as an organizer-confirmed score.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the repo root is importable when this file is run as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from src.metric import ALPHA, BETA, R_M
from src.submission_writer import GridSpec, write_submission, write_audit_json, write_zip
from src.validator import validate

DOWNLOADS = REPO_ROOT / "docs" / "downloads"
DEFAULT_SPEC = GridSpec.competition_default()

HYPOTHESIS = "baseline-dotted-budget"
MODE = "zeros-outside-footprint"  # every cell finite; zeros outside emission dots
NOTE = (
    "GEMSDOE72 baseline | format-valid submission package (single-band float32, "
    "EPSG:32611, 100 m, 3730x3292, values in [0,1], all finite, no nodata). "
    "Baseline dotted emission; competition training data not accessible from this "
    "sandbox so score is UNVERIFIED and not a leaderboard claim."
)


def content_digest8(arr: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(arr, dtype=np.float32).tobytes()).hexdigest()[:8]


def make_baseline_prediction(spec: GridSpec, budget_px: int = 6000, seed: int = 72) -> np.ndarray:
    """Fixed-budget dotted emission baseline on the competition grid.

    Places `budget_px` unit-probability dots on a perturbed regular lattice.
    Deterministic given `seed`.  Every other cell is 0.0.  All finite, in [0,1].
    """
    h, w = spec.shape
    rng = np.random.default_rng(seed)
    p = np.zeros((h, w), dtype=np.float64)

    step = int(np.sqrt((h * w) / budget_px)) or 1
    ys, xs = np.mgrid[step // 2:h:step, step // 2:w:step]
    cand_y = ys.ravel()
    cand_x = xs.ravel()
    if cand_y.size == 0:
        return p.astype(np.float32)
    jitter = (rng.random((2, cand_y.size)) - 0.5) * (step * 0.6)
    pick_y = np.clip(cand_y + jitter[0], 0, h - 1).astype(int)
    pick_x = np.clip(cand_x + jitter[1], 0, w - 1).astype(int)
    n = min(budget_px, pick_y.size)
    take = rng.choice(pick_y.size, size=n, replace=False)
    p[pick_y[take], pick_x[take]] = 1.0
    return p.astype(np.float32)


def main() -> None:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)

    p = make_baseline_prediction(DEFAULT_SPEC)
    digest8 = content_digest8(p)
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_name = f"gemsdoe72-{HYPOTHESIS}-{stamp}-{digest8}-{MODE}"

    tif_path = DOWNLOADS / f"{base_name}.tif"
    zip_path = DOWNLOADS / f"{base_name}.zip"
    audit_path = DOWNLOADS / f"{base_name}.audit.json"

    receipt = write_submission(p, tif_path, spec=DEFAULT_SPEC)
    receipt.update({
        "hypothesis": HYPOTHESIS,
        "mode": MODE,
        "note": NOTE,
        "content_digest8": digest8,
        "budget_px": int((p > 0).sum()),
        "generated_at_utc": stamp,
        "score_status": "UNVERIFIED baseline (not organizer-confirmed)",
        "ok_to_submit_format": True,
    })
    write_audit_json(receipt, audit_path)
    write_zip(tif_path, zip_path)

    vr = validate(tif_path)
    receipt["validator"] = {
        "passed": vr.passed,
        "message": vr.message,
        "checks": vr.checks,
    }

    manifest = {
        "submission_tif": tif_path.name,
        "zip": zip_path.name,
        "audit_json": audit_path.name,
        "sha256": receipt["sha256"],
        "shape": receipt["shape"],
        "crs": receipt["crs"],
        "transform": receipt["transform"],
        "dtype": receipt["dtype"],
        "budget_px": receipt["budget_px"],
        "score_status": receipt["score_status"],
        "ok_to_submit_format": receipt["ok_to_submit_format"],
        "validator_passed": vr.passed,
        "validator_message": vr.message,
        "generated_at_utc": stamp,
    }
    manifest_path = DOWNLOADS / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    print("=== GEMSDOE72 submission generated ===")
    print(f"TIF:           {tif_path}")
    print(f"ZIP:           {zip_path}")
    print(f"Audit:         {audit_path}")
    print(f"SHA256:        {receipt['sha256']}")
    print(f"Shape:         {receipt['shape']}  CRS: {receipt['crs']}")
    print(f"Dtype:         {receipt['dtype']}  nodata: {receipt['nodata']}")
    print(f"Budget px:     {receipt['budget_px']}  ({receipt['footprint_fraction']*100:.4f}% of grid)")
    print(f"Range [0,1]:   {receipt['in_footprint_range_0_1']}  All finite: {receipt['all_finite']}")
    print(f"Validator:     {'PASS' if vr.passed else 'FAIL'} -- {vr.message}")
    print(f"OK to submit (format): {receipt['ok_to_submit_format']}")
    print(f"Score status:  {receipt['score_status']}")
    print(f"Manifest:      {manifest_path}")


if __name__ == "__main__":
    main()
