#!/usr/bin/env bash
# Fetch 3DEP 1m DEM tiles via competition-provided 1m_DEM_links.csv
# Requires: data/1m_DEM_links.csv (from DrivenData login) → data/dem/
set -e
if [ ! -f data/1m_DEM_links.csv ]; then
  echo "Missing data/1m_DEM_links.csv — run bash scripts/download_competition_data.sh first (requires login)"
  exit 1
fi
mkdir -p data/dem
python3 -c "
import csv, pathlib, urllib.request
csv_path=pathlib.Path('data/1m_DEM_links.csv')
out=pathlib.Path('data/dem')
for row in csv.DictReader(open(csv_path)):
    url=row.get('url') or row.get('link') or list(row.values())[0]
    dest=out / pathlib.Path(url).name
    if dest.exists(): print('exists', dest)
    else:
        print('fetch', url)
        urllib.request.urlretrieve(url, dest)
print('done')
"
