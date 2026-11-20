"""Prepare native NAC observations and map their pixels to one approximate site-centered grid."""
from pathlib import Path
import sys, json, re, argparse, requests
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'reconstructed'))
from independent import setup,scan,Lines
import numpy as np
from shapely.geometry import Polygon,Point
from shapely import wkt

A='M1491897245LC';SAMPLE=2189.7645;LINE=34419.4267
PREF=[A,'M1435658799LC','M1448538445LC','M1433308510RC','M1524669573LC','M1367641457RC','M1335882808RC','M1512968740RC','M1481346260RC','M1509446289RC','M1398120658RC','M1124130817LC','M1420405483LC','M1463782498LC','M1500081055LC','M1515317029RC','M1515324043RC','M1507105139LC','M1519985562RC','M1385218373RC','M1385225417RC','M1405157120RC','M1530506944LC','M1532848972LC','M1532848972RC']
def meta(name):
    url='https://data.lroc.im-ldi.com/lroc/view_lroc/LRO-L-LROC-3-CDR-V1.0/'+name
    r=requests.get(url);r.raise_for_status();s=' '.join(re.sub('<[^>]+>',' ',r.text).split())
    def val(k):return float(re.search(re.escape(k)+r' (-?[\d.]+)',s)[1])
    return dict(date=re.search(r' Start time \(DOY:\d+\) ([\d:T-]+)',s)[1],original='https:'+next(k for k in re.findall(r'href="([^"]+?\.IMG)"',r.text) if '3-CDR' in k),incidence_deg=val('Incidence angle'),sun_lon=val('Sub solar longitude'),sun_lat=val('Sub solar latitude'),emission=val('Emission angle'),w_m=val('Scaled pixel width'),h_m=val('Scaled pixel height'),lines=int(val('Image lines')),samples=int(val('Line samples')),corners=[[val(k+' longitude'),val(k+' latitude')] for k in ['Upper left','Upper right','Lower left','Lower right']])

def setup_geo(infos):
    setup();scan.META=infos;scan.GRID=.95;m=infos[A];u,v=SAMPLE/(m['samples']-1),LINE/(m['lines']-1);ul,ur,ll,lr=np.array(m['corners'])
    pt=ul*(1-u)*(1-v)+ur*u*(1-v)+ll*(1-u)*v+lr*u*v
    scan.SCALE=np.array([scan.DEG*np.cos(np.deg2rad(pt[1])),-scan.DEG])
    scan.ORIGIN=pt-np.array([448,448])*scan.GRID/scan.SCALE
    return pt
def frame(n,root,raw):
    if (raw/(n+'.IMG')).exists():return scan.Frame(n,raw)
    m=scan.META[n];f=scan.Frame.__new__(scan.Frame);f.name=n;f.vertices=(np.array(m['corners'])-scan.ORIGIN)*scan.SCALE/scan.GRID
    f.footprint=Polygon(f.vertices[[0,1,3,2]]);f.h,f.w=m['lines'],m['samples'];f.image=Lines(m,root/'ranges');return f
def run(root,raw,ode,manifest=None):
    tiles=root/'tiles';tiles.mkdir(parents=True,exist_ok=True)
    mpath=root/'observations.json';infos=json.loads(mpath.read_text()) if mpath.exists() else {}
    if manifest:
        infos=json.loads(manifest.read_text());mpath.write_text(json.dumps(infos,indent=2));names=list(infos)
    elif ode:
        results=json.loads(ode.read_text())['Products']['Product']
        point=Point(276.99227-360,-6.10273)
        names=[r['Product_name'].split('.')[0] for r in results if float(r['Incidence_angle'])<94 and wkt.loads(r['Footprint_C0_geometry']).distance(point)<.016]
        names=list(dict.fromkeys(PREF+names))
    else:names=PREF
    for n in names:
        if n not in infos:infos[n]=meta(n);mpath.write_text(json.dumps(infos,indent=2))
        if (tiles/(n+'.npy')).exists():continue
        setup_geo(infos);a=frame(n,root,raw).tile(0,0);np.save(tiles/(n+'.npy'),a)
        print(n,infos[n]['date'],infos[n]['incidence_deg'],infos[n]['sun_lon'],int((a>100).sum()),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('raw',type=Path);p.add_argument('--ode',type=Path);p.add_argument('--manifest',type=Path)
    a=p.parse_args();run(a.folder,a.raw,a.ode,a.manifest)
