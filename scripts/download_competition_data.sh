#!/usr/bin/env bash
# Requires DrivenData login — run on unrestricted machine
set -e
echo "This script would download competition data if you have credentials."
echo "Manual: log in to https://www.drivendata.org/competitions/306/competition-doe-gems/data/ and save to data/"
echo "Expected: training_features.tif (418MB), labels.tif, sample_submission.tif, 1m_DEM_links.csv"
mkdir -p data
if [ -f data/training_features.tif ]; then
  echo "data/training_features.tif present $(du -h data/training_features.tif)"
fi
python3 scripts/prepare_data.py || echo "prepare_data.py not yet implemented — see GEMSDOE32/scripts/build_features.py"
