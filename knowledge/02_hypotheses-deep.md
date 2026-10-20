# Hypotheses deep dive

See docs/hypotheses.html for table.

## H72-A implementation

`src/gems72/h72.py`: synthetic_thk/cond/topo with 180 Walker Lane faults (N35W±14°, L120-340px), Roberts cross (Th/K edge), Sobel (cond grad), divergence σ=10px (1km arch), zero-crossing σ=2px, robust-unit (median/IQR), fuse √(halo·topo), agree via dilation 4/6px, greedy 2px spacing, 2px catalogue buffer.

Why ranking: expected +0.007-0.015 drift DTI, low cost (already mirrored).

## Leakage canary

Each feature alone on blocked holdout: edge 0.58, cond 0.62, divergence 0.68, zero-cross 0.57 — none >0.90 → no leakage.

## Cost/obtainability

- H72-A: low, uses geodawn_rad_u8 (27132925 bytes, sha256 a35a9cd..., already in GEMSDOE24 data/external)
- H72-C: medium, needs 3DEP 1m DEM via 1m_DEM_links.csv (login, free USGS, ~2GB) — scripts/fetch_3dep.sh
- H72-D: high, needs GDR 1391 CSV (DOI 10.15121/1881483, CC BY, free) — scripts/fetch_gdr.sh

All sources official, verified.

## Verification line-by-line

- Metric: fetched problem page twice, reproduced 0.60 worked example in tests/test_metric.py
- Transform: [100,0,243350,0,-100,4508550] from sample_submission.tif re-read, verified on 5 sibling repos
- Footprint: 5,167,373 finite pixels from sample_submission.tif NaN (same as our nan twin)
- CRS: EPSG:32611 via epsg.io/32611
- Leaderboard: read 2026-10-20, #1 0.3262 nchuzhoy (2 snapshots)
- Rules PDF: nl.gov/96647 50d854b1e0239fe6...
