from images import *
from terrain import features, match
import numpy as np
import cv2
import pandas as pd
import sys
def run(root,loc,out):
    out.mkdir(exist_ok=True,parents=True);m=json.loads((root/'observations.json').read_text())
    coords=json.loads((loc/'centers.json').read_text())
    supplemental=root/'first/centers.json'
    if supplemental.exists():coords={**json.loads(supplemental.read_text()),**coords}
    if (out/'centers.json').exists():coords={**coords,**json.loads((out/'centers.json').read_text())}
    descs={}
    def im(n):return np.load(root/'tiles'/(n+'.npy'))
    def ft(n,channel='band'):
        if (n,channel) not in descs:descs[n,channel]=features(im(n),channel)
        return descs[n,channel]
    links=[]
    # Anchors and successors are ordered by dates and lighting rather than target contrast.
    for f,n in [('M1481346260RC','M114498484RC'),('M1481346260RC','M1422745700LC'),('M1512968740RC','M1398120658RC'),('M1512968740RC','M1500081055LC'),('M1500081055LC','M1515317029RC'),('M1500081055LC','M1515324043RC'),('M1500081055LC','M1385218373RC'),('M1500081055LC','M1385225417RC'),('M1512968740RC','M1367641457RC'),('M1524669573LC','M1367641457RC')]:
        if f not in coords or not (root/'tiles'/(n+'.npy')).exists():continue
        p=np.array([coords[f]['x'],coords[f]['y']])
        for m1,m2 in [('band','band'),('band','negative'),('gradient','gradient')]:
            r=match(ft(f,m1),ft(n,m2),p)
            if r is None:continue
            q,s=r
            if any(q<30) or any(q>1314):continue
            rec=dict(from_product=f,destination=n,x=q[0],y=q[1],mode=m2,cost=s['p90']+coords[f]['cost'],**s)
            links.append(rec);coords[n]=rec;print(n,f,s['n'],q,flush=True);break
    (out/'centers.json').write_text(json.dumps(coords,indent=2))
    pd.DataFrame(links).to_csv(out/'pair-links.csv',index=False)
if __name__=='__main__':run(*[Path(k) for k in sys.argv[1:]])
