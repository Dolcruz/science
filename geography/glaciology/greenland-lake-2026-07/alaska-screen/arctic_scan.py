"""Screen Arctic Alaskan lake basins for persistent recent open-water loss."""
from pathlib import Path
from datetime import date
import argparse,hashlib,json
import numpy as np
import pandas as pd
import requests
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import xy
from pyproj import Transformer
from scipy import ndimage as ndi

base=Path(__file__).resolve().parent
tiles=['04WFD','04WED','05WNU','03WXU','03WWP']
years=range(2023,2027)
api='https://earth-search.aws.element84.com/v1/search'

def inventory(tile,year):
    path=base/f'inventory-{tile}-{year}.json'
    if path.exists():return json.loads(path.read_text())
    req={'collections':['sentinel-2-c1-l2a'],'datetime':f'{year}-07-14T00:00:00Z/{year}-08-27T23:59:59Z','query':{'mgrs:utm_zone':{'eq':int(tile[:2])},'mgrs:latitude_band':{'eq':tile[2]},'mgrs:grid_square':{'eq':tile[3:]}},'limit':100}
    st=requests.post(api,json=req);st.raise_for_status();j=st.json()
    rows=j['features']; count=j['numberMatched']
    while len(rows)<count:
        nx=next(a for a in j['links'] if a['rel']=='next')
        u=requests.post(nx['href'],json=nx['body']) if nx.get('method')=='POST' else requests.get(nx['href'])
        u.raise_for_status();j=u.json();rows.extend(j['features'])
    assert len(rows)==count
    items=[]
    for a in rows:
        p=a['properties'];items.append(dict(id=a['id'],tile=tile,date=p['datetime'][:10],cloud=p['eo:cloud_cover'],nodata=p['s2:nodata_pixel_percentage'],snow=p.get('s2:snow_ice_percentage',0),assets={k:{k1:v1 for k1,v1 in a['assets'][k].items() if k1 in ('href','file:checksum','file:size','raster:bands','proj:transform')} for k in ('scl','green','red','blue','nir','swir16')}))
    path.write_text(json.dumps(items));return items

def scan(tile):
    pdir=base/'scl';pdir.mkdir(exist_ok=True)
    water=[];land=[];selected=[]
    for year in years:
        inv=inventory(tile,year);pick=[]
        for r in sorted(inv,key=lambda d:d['cloud']+d['nodata']+d['snow']):
            if r['nodata']>55 or any(abs((date.fromisoformat(r['date'])-date.fromisoformat(s['date'])).days)<5 for s in pick):continue
            pick.append(r)
            if len(pick)==3:break
        units=[]
        for r in pick:
            a=r['assets']['scl'];path=pdir/(r['id']+'.tif')
            if not path.exists():
                res=requests.get(a['href']);res.raise_for_status();b=res.content
                assert len(b)==a['file:size'] and '1220'+hashlib.sha256(b).hexdigest()==a['file:checksum']
                path.write_bytes(b)
            with rasterio.open(path) as src:
                # An exact 60 m grid, aligned at the 20 m SCL origin.
                band=src.read(1).reshape(1830,3,1830,3)
                w=(band==6).sum(axis=(1,3));l=((band==4)|(band==5)).sum(axis=(1,3))
                units.append([w>=5,l>=5])
                transform=src.transform*src.transform.scale(3,3);epsg=src.crs.to_epsg()
        if len(units)<2:
            water.append(np.zeros((1830,1830),bool));land.append(np.zeros_like(water[-1]))
        else:
            water.append(np.sum([a[0] for a in units],axis=0)>=2)
            land.append(np.sum([a[1] for a in units],axis=0)>=2)
        selected.extend(pick);print(tile,year,len(inv),[r['date'] for r in pick],flush=True)
    (base/(tile+'-pick.json')).write_text(json.dumps(selected))
    np.savez_compressed(base/(tile+'-water.npz'),water=water,land=land)
    transf=Transformer.from_crs(epsg,4326,always_xy=True)
    rows=[]
    for t in range(1,len(years)):
        a,b=water[t-1],land[t]
        labels,n=ndi.label(a,structure=np.ones((3,3)))
        sizes=np.bincount(labels.ravel());loss=np.bincount(labels[b],minlength=n+1)
        sites=np.flatnonzero((sizes>=12)&(sizes<=5000)&(loss>=12)&(loss>.50*sizes))
        objects=ndi.find_objects(labels)
        for lab in sites:
            if lab==0:continue
            sl=objects[lab-1];reg=labels[sl]==lab
            # Use the deepest interior cell for later acquisition and image centering.
            yy,xx=np.unravel_index(ndi.distance_transform_edt(np.pad(reg,1))[1:-1,1:-1].argmax(),reg.shape)
            row,col=sl[0].start+yy,sl[1].start+xx
            e,north=xy(transform,row,col);lon,lat=transf.transform(e,north)
            wfrac=[float(x[sl][reg].mean()) for x in water];lfrac=[float(x[sl][reg].mean()) for x in land]
            rows.append(dict(tile=tile,year=2023+t,initial_km2=sizes[lab]*.0036,dry_km2=loss[lab]*.0036,fraction=loss[lab]/sizes[lab],lon=lon,lat=lat,e=e,n=north,row=row,col=col,label=lab,water=wfrac,land=lfrac,
                width=(sl[1].stop-sl[1].start)*60,height=(sl[0].stop-sl[0].start)*60,
                score=loss[lab]/sizes[lab]*min(lfrac[t:])*min(wfrac[:t])*np.sqrt(loss[lab])))
    df=pd.DataFrame(rows)
    if len(df):df.sort_values('score',ascending=False,inplace=True)
    df.to_csv(base/(tile+'-candidates.csv'),index=False)
    if len(df):print(df[['tile','year','dry_km2','fraction','lat','lon','score']].head(6).to_string(index=False),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('tiles',nargs='*');a=parser.parse_args()
    for tile in (a.tiles or tiles):scan(tile)
