"""Locate the center in independent NAC acquisitions using only surrounding landmarks."""
from images import HERE,A,scan,setup_geo,frame
from terrain import features, match
import cv2
import numpy as np
import pandas as pd
import json,sys
from pathlib import Path
def go(root,out):
    out.mkdir(parents=True,exist_ok=True)
    refs=root/'tiles';meta=json.loads((root/'observations.json').read_text())
    center=np.array([672.,672.]);data={A:dict(x=672.,y=672.,cost=0.,from_product='',n=0,checks=0,p90=0.)};rows=[]
    cache={}
    def key(k,m):
        if (k,m) not in cache:cache[k,m]=features(np.load(refs/(k+'.npy')),m)
        return cache[k,m]
    def longitude(n):return ((meta[n]['sun_lon']-276.99+180)%360)-180
    # Use same-illumination calibrators first. Revisit images with no initial path.
    names=[p.stem for p in refs.glob('*.npy')]
    targets=sorted((n for n in names if n!=A),key=lambda n:abs(longitude(n)-longitude(A)))
    for cycle in range(2):
        improved=False
        for n in targets:
            if n in data:continue
            opts=[]
            # A comparable phase and many off-target ties provide a direct route.
            anchors=sorted(data,key=lambda k:abs(longitude(k)-longitude(n))+.8*data[k]['cost'])
            for f in anchors:
                if opts and opts[0][0]<1.25:break
                for mode in (["band"] if abs(longitude(f)-longitude(n))<35 else ["band","negative","gradient"]):
                    p=np.array([data[f]['x'],data[f]['y']])
                    if np.linalg.norm(p-672)>900:continue
                    r=match(key(f,'gradient' if mode=='gradient' else 'band'),key(n,mode),p)
                    if r is None:continue
                    q,s=r
                    if any(q<65) or any(q>1278):continue
                    rec=dict(destination=n,from_product=f,x=q[0],y=q[1],cost=s['p90']+data[f]['cost'],mode=mode,**s)
                    opts.append((rec['cost'],rec));rows.append(rec)
                    if rec['cost']<1.25:break
                # A well-sampled anchor with subpixel local check is adequate for forwarding.
                if opts and opts[-1][1]['near']>=24 and opts[-1][1]['p90']<1.5:break
            if opts:
                rec=min(opts,key=lambda q:q[0])[1];data[n]=rec;improved=True
                print(n,rec['from_product'],rec['n'],round(rec['cost'],2),round(rec['x'],2),round(rec['y'],2),flush=True)
                (out/'centers.json').write_text(json.dumps(data,indent=2));pd.DataFrame(rows).to_csv(out/'links.csv',index=False)
        if not improved:break
    (out/'failed.txt').write_text('\n'.join(n for n in names if n not in data)+'\n')
if __name__=='__main__':go(Path(sys.argv[1]),Path(sys.argv[2]))
