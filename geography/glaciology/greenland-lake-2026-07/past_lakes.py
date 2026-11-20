"""Cross-match July 2026 water footprints with two historical lake archives."""
from io import BytesIO
import json, hashlib
import requests
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from fetch import ROOT, DATA
from measure import PEAK, optical
from zipfile import ZipFile
from pathlib import Path
import shapefile
from shapely.geometry import shape, box
from shapely.ops import transform, unary_union
from pyproj import Transformer
import pandas as pd

AREA=box(604400,7446400,608400,7449600)
ut=Transformer.from_crs(4326,32622,always_xy=True)
def match():
    DATA.mkdir(parents=True,exist_ok=True)
    for record,file,md5 in [(16577959,"Meltwater_Features_V3.zip","7a4183d2ead241e13a9d6199533cbfee"),
                            (4813833,"lakes.zip","b9fec63f1443d4c3d33ab03fbcd258be")]:
        path=DATA/file
        if not path.exists():
            response=requests.get(f"https://zenodo.org/api/records/{record}/files/{file}/content")
            response.raise_for_status()
            if hashlib.md5(response.content).hexdigest()!=md5:
                raise ValueError(f"Archive checksum mismatch for {file}")
            path.write_bytes(response.content)
        if hashlib.md5(path.read_bytes()).hexdigest()!=md5:
            raise ValueError(f"Archive checksum mismatch for {file}")
    with np.load(ROOT/"measurement-chips.npz") as chips:
        raw={k:chips[PEAK+"_"+k].reshape(320,400) for k in ["blue","red","scl"]}
    water,valid=optical(raw,"s2")
    current=(water>.25)&valid
    def overlap(poly):
        if poly.is_empty:return 0.
        old=rasterize([(poly,1)],out_shape=current.shape,transform=from_origin(604400,7449600,10,10))
        return np.sum(current & (old==1))*.0001
    rows=[]
    with ZipFile(DATA/'Meltwater_Features_V3.zip') as z:
        for shp in z.namelist():
            if '/Large_Lakes/' not in shp or not shp.endswith('.shp') or shp.startswith('__MACOSX'):continue
            name=shp[:-4]
            rd=shapefile.Reader(shp=BytesIO(z.read(name+'.shp')),shx=BytesIO(z.read(name+'.shx')),dbf=BytesIO(z.read(name+'.dbf')))
            polys=[shape(r.__geo_interface__) for r in rd.iterShapes(bbox=AREA.bounds)]
            union=unary_union(polys).intersection(AREA)
            if union.area>.0495e6:
                rows.append(dict(catalog='Russell–Leverett',record=shp,period=shp.split('/')[2][3:11],area_km2=union.area/1e6,overlap_2026_km2=overlap(union)))
    with ZipFile(DATA/'lakes.zip') as z:
        for year in [2018,2019]:
            name=f'lakes/surface/surface_SW{year}.geojson'
            polys=[]
            for rec in json.loads(z.read(name))['features']:
                poly=shape(rec['geometry'])
                a,b,c,d=poly.bounds
                if a>-48.4 or c<-48.7 or d<67.06 or b>67.2:continue
                q=transform(ut.transform,poly).intersection(AREA)
                if not q.is_empty:polys.append(q)
            rows.append(dict(catalog='Pan-Greenland',record=name,period=str(year),area_km2=unary_union(polys).area/1e6,overlap_2026_km2=overlap(unary_union(polys))))
    t=pd.DataFrame(rows);t.to_csv(ROOT/'historical.csv',index=False)
    print(t.sort_values('area_km2',ascending=False).head(8).to_string(index=False))
    print(t.tail(2).to_string(index=False))
if __name__=='__main__':match()
