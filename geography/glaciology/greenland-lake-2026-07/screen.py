"""Reproduce the 80 m regional water-loss screen on the archived Sentinel-2 scenes."""
import json
from datetime import date

import certifi
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from scipy import ndimage as nd
from pyproj import Transformer

from fetch import DATA, ROOT

AREA=(568000,7428000,608000,7452000)


def coarse(obs):
    path=DATA/"coarse-2026"/(obs["id"]+".npz")
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        arr={}
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",CURL_CA_BUNDLE=certifi.where()):
            for key,href in obs["assets"].items():
                with rasterio.open(href) as ds:
                    v=ds.read(1,window=from_bounds(*AREA,transform=ds.transform),out_shape=(300,500))
                if key!="scl":
                    nodata=v==0
                    v=v.astype("f4")*.0001-.1
                    v[nodata]=np.nan
                arr[key]=v
        np.savez_compressed(path,**arr)
    with np.load(path) as arr:
        b,r=arr["blue"],arr["red"]
        index=(b-r)/(b+r+.0001)
        good=np.isfinite(index)&~np.isin(arr["scl"],[0,3,8,9,10])
        return (index>.23)&good,good


def run():
    obs=json.loads((ROOT/"screen-scenes.json").read_text())
    frames=[coarse(o) for o in obs]
    rows=[]
    projection=Transformer.from_crs(32622,4326,always_xy=True)
    for i,(water,_) in enumerate(frames):
        labels,_=nd.label(water,structure=np.ones((3,3)))
        for label,slab in enumerate(nd.find_objects(labels),1):
            if slab is None:continue
            y,x=np.where(labels[slab]==label)
            if not 25<=len(x)<=1200:continue
            y+=slab[0].start
            x+=slab[1].start
            for j in range(i+1,len(frames)):
                t0,t1=[date.fromisoformat(obs[k]["date"]) for k in (i,j)]
                if (t1-t0).days>8:break
                post,valid=frames[j]
                fraction=post[y,x].mean()
                if valid[y,x].mean()<=.9 or fraction>.2:continue
                e=AREA[0]+(x.mean()+.5)*80
                n=AREA[3]-(y.mean()+.5)*80
                lon,lat=projection.transform(e,n)
                rows.append(dict(start=t0.isoformat(),end=t1.isoformat(),water_pixels=len(x),
                                 remaining_fraction=fraction,longitude=lon,latitude=lat))
    pd.DataFrame(rows).sort_values("water_pixels",ascending=False).to_csv(ROOT/"regional-screen.csv",index=False)


if __name__=="__main__":
    run()
