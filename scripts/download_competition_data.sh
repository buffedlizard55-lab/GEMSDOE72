#!/usr/bin/env bash
# download_competition_data.sh
#
# GEMS Prize Challenge (DrivenData #306) data placement.
#
# BLOCKER: the competition training data (training_features.tif, labels.tif,
# sample_submission.tif, 1m_DEM_links.csv) lives on the login-walled DrivenData
# data download page:
#   https://www.drivendata.org/competitions/306/competition-doe-gems/data/
# This sandbox cannot authenticate to DrivenData (verified redirect to login),
# and the Dropbox mirrors referenced in the brief are not reachable from the
# allowed egress hosts.  Therefore this script CANNOT auto-download the data.
#
# Instead, run this on ANY unrestricted machine with DrivenData access, then
# copy the resulting data/ directory into this repository:
#
#   1. Log in to https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#   2. Download into data/:
#        training_features.tif   (19 bands, float32, EPSG:32611, 100 m,
#                                 3292 x 3730, nodata -3.4028234663852886e+38)
#        labels.tif              (int32 fault mask, nodata -1)
#        sample_submission.tif   (format template: all-zeros, same grid)
#        1m_DEM_links.csv        (1 m DEM download URLs)
#   3. Verify grid: rasterio reports Width 3292, Height 3730, CRS EPSG:32611,
#      res 100x100 for both training_features.tif and labels.tif.
#   4. Copy data/ into this repo root (data/ is gitignored; do not commit it).
#
# After data placement:
#   python scripts/prepare_data.py    # build the cached feature stack
#   python -m pytest tests/ -q        # verify the DTI metric (worked example 0.60)
#   # train -> validate on the spatially-blocked holdout -> generate submission
#
set -euo pipefail

echo "This script is a placeholder documenting manual data placement."
echo "DrivenData competition data is login-walled and cannot be fetched from this sandbox."
echo "See https://www.drivendata.org/competitions/306/competition-doe-gems/data/"
exit 0
