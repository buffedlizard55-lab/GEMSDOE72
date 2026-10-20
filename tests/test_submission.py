import pathlib, sys
import numpy as np, rasterio
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"src"))
from gems72.grid import check_submission
def test_submission_format():
    tif=next(pathlib.Path("docs/downloads").glob("*zeros.tif"))
    tpl=pathlib.Path("/tmp/GEMSDOE32/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    with rasterio.open(tpl) as s: foot=np.isfinite(s.read(1))
    receipt=check_submission(tif, foot)
    assert receipt["ok_range"], receipt
    assert receipt["finite_inside"]==receipt["footprint_px"]
    assert receipt["positive_px"]==42000
    assert 0 <= receipt["min_in"] <= receipt["max_in"] <= 1.0
