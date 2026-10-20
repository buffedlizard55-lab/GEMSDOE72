# scripts

Data preparation for the GEMS Prize Challenge submission pipeline.

## The single remaining blocker: data placement

The competition training data is **login-walled on DrivenData**:
https://www.drivendata.org/competitions/306/competition-doe-gems/data/

This sandbox cannot authenticate to DrivenData, so `training_features.tif`,
`labels.tif`, `sample_submission.tif` and `1m_DEM_links.csv` must be placed in
`data/` manually from an unrestricted machine (see
`scripts/download_competition_data.sh`). `data/` is gitignored and must not be
committed.

## Expected pipeline (run after data is in data/)

1. `python scripts/prepare_data.py` — build the cached feature stack from
   `training_features.tif` + `labels.tif`.
2. `python -m pytest tests/ -q` — verify the distance-weighted Tversky index
   reproduces the published worked example (TPw=3.00, FPw=1.89, FNw=2.00 -> 0.60).
3. Train / validate on the spatially-blocked holdout (hide whole fault segments
   with a buffer; derive catalogue-based features only from visible faults;
   score pooled DTI, alpha 0.2, beta 0.8, 300 m triangular kernel).
4. `python src/generate_submission.py` — write a format-valid GeoTIFF + audit
   receipt + zip into `docs/downloads/`.
5. Validate the output with `src.validator` before offering it for download.

## Notes

- Metric: distance-weighted Tversky index, alpha=0.2, beta=0.8, triangular
  kernel R=300 m (3 px at 100 m). Implementation in `src/metric.py`.
- Submission grid (competition): EPSG:32611, 100 m, 3730 x 3292,
  transform [100, 0, 243350, 0, -100, 4508550] (verified against the
  format-validated GEMSDOE32 audit receipt for the same competition).
- Values must be finite and in [0, 1]; no nodata tag (a float32 -3.4e38 nodata
  sentinel triggers the DrivenData "Predicted values must be in range [0, 1]"
  error).
