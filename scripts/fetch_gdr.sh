#!/usr/bin/env bash
# Fetch GDR 1391 wells/springs CSV (free CC BY 4.0)
set -e
mkdir -p data/external
url="https://gdr.openei.org/files/1391/Nevada_Well_and_Spring_Temperature_and_Chemistry_Data.csv"
echo "Fetching $url"
curl -L -o data/external/gdr_wellspring.csv "$url" || wget -O data/external/gdr_wellspring.csv "$url"
ls -lh data/external/gdr_wellspring.csv
sha256sum data/external/gdr_wellspring.csv
