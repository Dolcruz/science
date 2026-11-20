"""Calculate open-water areas, comparison-pool persistence and radar contrasts."""
import numpy as np
import pandas as pd
from scipy import ndimage as nd
from pyproj import Transformer

from fetch import ROOT, OBS, SCALE, WEST, NORTH, product_path

THRESHOLDS = (.20, .25, .30)
PEAK = "S2C_22WFV_20260720_0_L2A"
TO_WGS = Transformer.from_crs(32622,4326,always_xy=True)


def optical(raw, instrument):
    blue = raw["blue"].astype(float)
    red = raw["red"].astype(float)
    valid = (blue > 0) & (red > 0)
    if instrument == "s2":
        scale, offset = .0001, -.1
        valid &= ~np.isin(raw["scl"], [0, 3, 8, 9, 10])
    else:
        scale, offset = .0000275, -.2
        valid &= (raw["qa_pixel"] & 31) == 0
    ndwi = ((blue-red)*scale) / ((blue+red)*scale+2*offset+.0001)
    return ndwi, valid


def window(shape, step):
    y, x = np.indices(shape)
    return (x*step >= 3200) & (x*step < 7200) & (y*step >= 1800) & (y*step < 5000)


def blocks(mask):
    h,w = mask.shape
    return mask.reshape(h//2,2,w//2,2).mean(axis=(1,3)) >= .75


def prepare(index, valid):
    y,x = np.indices(index.shape)
    region = window(index.shape,10)
    ref = region & (index>.25) & valid
    dry = region & ~nd.binary_dilation(index>.25,iterations=30) & valid
    core_roi = (x>=350) & (x<695) & (y>=276) & (y<490)
    core = nd.binary_erosion((index>.34) & valid & core_roi,iterations=5)[::2,::2]
    # Comparison centers are selected on the peak date alone.
    opened = nd.binary_opening((index>.35)&valid,structure=np.ones((5,5)))
    labels, _ = nd.label(opened)
    disks=[]
    for i, slab in enumerate(nd.find_objects(labels),1):
        if slab is None:
            continue
        component = labels[slab] == i
        if component.sum() < 1800:
            continue
        interior = nd.distance_transform_edt(np.pad(component,1))[1:-1,1:-1]
        if interior.max() < 12:
            continue
        iy, ix = np.unravel_index(interior.argmax(),interior.shape)
        cy, cx = slab[0].start+iy, slab[1].start+ix
        lon,lat = TO_WGS.transform(WEST+(cx+.5)*10,NORTH-(cy+.5)*10)
        disks.append((int(cx),int(cy),lon,lat,(x-cx)**2+(y-cy)**2<=12**2))
    return ref, blocks(ref), blocks(dry), core, disks


def run():
    records=[]; radar=[]; comparisons=[]; sample={}
    ref_obs=next(o for o in OBS if o["id"]==PEAK)
    with np.load(product_path(ref_obs)) as raw:
        ref, foot, dry, core, disks = prepare(*optical(raw,"s2"))
    y,x=np.where(ref)
    print("Peak water centroid:",TO_WGS.transform(WEST+(x.mean()+.5)*10,NORTH-(y.mean()+.5)*10))
    sample["radar_foot"]=foot
    sample["radar_dry"]=dry
    for o in OBS:
        instr=o["instrument"]
        step=SCALE[instr]
        with np.load(product_path(o)) as raw:
            if instr=="s1":
                v=raw["hh"]
                good=(v>0)&np.isfinite(v)
                density=nd.uniform_filter(good.astype(float),5)
                smoothed=nd.uniform_filter(np.where(good,v,0.).astype(float),5)
                use=(density>.99999)&good
                if not np.any(use&foot) or not np.any(use&dry):
                    radar.append(dict(id=o["id"],time=o["time"],orbit=o["relative_orbit"],coverage=0.))
                    continue
                db=10*np.log10(np.maximum(smoothed,1e-10))
                baseline=float(np.median(db[use&dry]))
                diff=db-baseline
                row=dict(id=o["id"],time=o["time"],orbit=o["relative_orbit"],
                         coverage=(use&foot).sum()/foot.sum(),footprint_km2=foot.sum()*.0004,
                         median_delta_db=np.median(diff[use&foot]),dry_db=baseline)
                for cut in (3.,4.5,6.):
                    row[f"foot_below_{cut:g}dB"]=np.mean(diff[use&foot] < -cut)
                    row[f"dry_below_{cut:g}dB"]=np.mean(diff[use&dry] < -cut)
                if np.any(core&good):
                    row["core_hh_db"]=10*np.log10(np.median(v[core&good]))
                radar.append(row)
                if o["time"][8:10] in ["20","22","23"] and row["coverage"]>.95:
                    sample[o["id"]+"_hh"]=v
                continue

            index,valid=optical(raw,instr)
            roi=window(index.shape,step)
            row=dict(id=o["id"],time=o["time"],clear_fraction=np.mean(valid[roi]))
            for t in THRESHOLDS:
                row[f"water_km2_{t:.2f}"]=(np.sum(roi&valid&(index>t))*step**2/1e6
                                          if row["clear_fraction"]>0 else np.nan)
            records.append(row)
            if instr=="s2":
                for cx,cy,lon,lat,mask in disks:
                    good=mask&valid
                    comparisons.append(dict(id=o["id"],time=o["time"],x=cx,y=cy,longitude=lon,
                                            latitude=lat,clear_fraction=good.sum()/mask.sum(),
                                            water_fraction=np.mean(index[good]>.25) if good.any() else np.nan))
            if o["id"] in [PEAK,"S2C_22WFV_20260716_0_L2A","S2C_22WFV_20260723_0_L2A",
                            "LC09_L2SP_008013_20260721_02_T1","LC09_L2SP_006013_20260723_02_T1"]:
                for k in ("blue","red","scl" if instr=="s2" else "qa_pixel"):
                    sample[o["id"]+"_"+k]=raw[k][roi].copy()
    pd.DataFrame(records).to_csv(ROOT/"optical.csv",index=False)
    pd.DataFrame(radar).to_csv(ROOT/"radar.csv",index=False)
    pd.DataFrame(comparisons).to_csv(ROOT/"controls.csv",index=False)
    np.savez_compressed(ROOT/"measurement-chips.npz",**sample)


if __name__=="__main__":
    run()
