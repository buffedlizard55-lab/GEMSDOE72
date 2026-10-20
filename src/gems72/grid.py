"""Competition grid geometry, footprint, raster IO.
EPSG:32611, 100m, 3292x3730, origin (243350,4508550), footprint 5,167,373 px
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, rasterio
NODATA_F32=np.float32(-3.4028234663852886e38)
TEMPLATE=dict(driver="GTiff",dtype="float32",count=1,crs="EPSG:32611",transform=None,width=3292,height=3730,nodata=np.nan)
def open_template(path: str|Path)->dict:
    with rasterio.open(path) as s:
        return dict(driver="GTiff",dtype="float32",count=1,crs=s.crs,transform=s.transform,width=s.width,height=s.height,nodata=np.nan)
def read_footprint(features_path: str|Path, band:int=1)->np.ndarray:
    with rasterio.open(features_path) as s: a=s.read(band)
    return np.isfinite(a) & (a > NODATA_F32*np.float32(0.5))
def read_labels(path: str|Path)->np.ndarray:
    with rasterio.open(path) as s: a=s.read(1)
    return a>=1
def read_band(path: str|Path, band:int, fill:float=0.0)->np.ndarray:
    with rasterio.open(path) as s: a=s.read(band).astype(np.float32)
    return np.where(a < NODATA_F32*np.float32(0.5), np.float32(fill), a)
def write_submission(mask: np.ndarray, template_path: str|Path, out_path: str|Path, footprint: np.ndarray|None=None, outside: str="nan")->Path:
    meta=open_template(template_path); out=np.asarray(mask,dtype=np.float32)
    assert out.shape==(meta["height"],meta["width"]), (out.shape, meta)
    if footprint is not None:
        vals=out[footprint]
        assert np.isfinite(vals).all(), "non-finite inside footprint"
        assert (vals>=0).all() and (vals<=1).all(), "value outside [0,1] inside footprint"
        out=np.where(footprint,out, np.nan if outside=="nan" else np.float32(0.0))
    outside_vals=out[~footprint] if footprint is not None else None
    if outside_vals is not None and outside=="nan": assert np.isnan(outside_vals).all()
    meta["nodata"]=np.nan; meta["compress"]="deflate"; meta["tiled"]=True
    out_path=Path(out_path); out_path.parent.mkdir(parents=True,exist_ok=True)
    with rasterio.open(out_path,"w",**meta) as dst: dst.write(out,1)
    return out_path
def valid_range_mask(arr: np.ndarray)->np.ndarray:
    a=np.asarray(arr); return np.isfinite(a) & (a>=0.0) & (a<=1.0)
def check_submission(path: str|Path, footprint: np.ndarray)->dict:
    import hashlib
    with rasterio.open(path) as s:
        a=s.read(1); meta=dict(crs=str(s.crs),width=s.width,height=s.height,transform=tuple(s.transform)[:6],dtype=s.dtypes[0],nodata=s.nodata)
    finite_in=np.isfinite(a[footprint]); in_range_in=finite_in & (a[footprint]>=0)&(a[footprint]<=1); outside=a[~footprint]
    h=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return dict(path=str(path),sha256=h,bytes=Path(path).stat().st_size,meta=meta,footprint_px=int(footprint.sum()),finite_inside=int(finite_in.sum()),in_range_inside=int(in_range_in.sum()),outside_nan=int(np.isnan(outside).sum()),outside_zero=int((outside==0).sum()),outside_other=int((~np.isnan(outside)&(outside!=0)).sum()),positive_px=int(((a>0)&footprint).sum()),min_in=float(np.nanmin(a[footprint])),max_in=float(np.nanmax(a[footprint])),ok_range=bool(in_range_in.sum()==finite_in.sum()==int(footprint.sum())),ok_outside=bool(np.isnan(outside).all() or (outside==0).all()))
def sha256(path: str|Path)->str:
    import hashlib; h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1<<20), b""): h.update(chunk)
    return h.hexdigest()
