#!/usr/bin/env bash
# Download competition data into data/  (run on an unrestricted, logged-in machine).
#
# BLOCKER (verified): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
# redirects to a login page; this sandbox has no DrivenData auth, so the files
# cannot be fetched automatically here. The Dropbox mirrors pasted into the
# project brief are not reachable from this sandbox either (outbound internet
# is limited to github.com / pypi.org / etc.).
#
# Steps (manual, once):
#   1. Log in to DrivenData, enroll in the GEMS Prize Challenge (#306).
#   2. Open https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#   3. Download into this repo's data/:
#        training_features.tif, labels.tif, sample_submission.tif,
#        existing_faults.tif, 1m_DEM_links.csv
#   4. Run: python scripts/prepare_data.py
#
# Public mirrors referenced by the brief (login-walled/redirect; verify before use):
#   https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?...&dl=1
#   https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?...&dl=1
#   https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?...&dl=1
#
# Official public data sources (no login) useful as external features:
#   GeoDAWN USGS data release:  https://doi.org/10.5066/P93LGLVQ
#                              https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
#                              https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7
#   INGENIOUS compilation (GDR):  https://gdr.openei.org/submissions/1391
#                                 https://doi.org/10.15121/1881483
#   USGS Quaternary Faults:       https://www.usgs.gov/programs/nhp/ (Quaternary Fault and Fold Database)
#   EPSG 32611:                   https://epsg.io/32611
#
set -euo pipefail
echo "This script documents the download step; it performs no network fetch."
echo "See comments above. After placing files in data/, run: python scripts/prepare_data.py"
