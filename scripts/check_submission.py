#!/usr/bin/env python3
import pathlib, sys
import numpy as np, rasterio
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"src"))
from gems72.grid import check_submission, sha256
tpl=pathlib.Path("/tmp/GEMSDOE32/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
with rasterio.open(tpl) as s: foot=np.isfinite(s.read(1))
for tif in pathlib.Path("docs/downloads").glob("*.tif"):
    print(check_submission(tif, foot))
    print("sha256", sha256(tif))
