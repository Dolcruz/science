"""Link opposite illumination groups with inverted high-pass and unsigned gradient images."""
import json
import sys
from pathlib import Path
from terrain import features, match
import numpy as np
import pandas as pd
def run(folder,out):
    coords=dict(np.load(out/'projected-centers.npz'))
    edges=[];best=json.loads((out/'best-links.json').read_text())
    cache={}
    def desc(n,mode):
        if (n,mode) not in cache:cache[n,mode]=features(np.load(folder/(n+'.npy')),mode)
        return cache[n,mode]
    # The 33-degree west-lit frame transfers across to east-lit terrain.
    # Once an east-lit anchor is available, ordinary band-pass views suffice.
    order=['M1229246404RC','M1168044929RC','M178510938LC','M1185701417RC','M1109154536RC','M1186879028LC']
    for n in order:
        options=[]
        for f in list(coords):
            if f==n or f not in ['M1191587829LC','M1176284678RC','M1526159508RC']+order:continue
            for m1,m2 in [('band','band'),('band','negative'),('gradient','gradient')]:
                r=match(desc(f,m1),desc(n,m2),coords[f])
                if r is None:continue
                q,st=r;cost=st['p90']+best.get(f,{}).get('cost',0)
                rec=dict(source=f,destination=n,channel=m2,qx=float(q[0]),qy=float(q[1]),cost=cost,**st)
                edges.append(rec);options.append((cost,q,rec))
        if options:
            _,q,rec=min(options,key=lambda r:r[0]);coords[n]=q;best[n]=rec;print(n,rec,flush=True)
        else:print(n,'no link',flush=True)
        np.savez_compressed(out/'cross-sun-centers.npz',**coords)
        (out/'cross-sun-links.json').write_text(json.dumps(best,indent=2));pd.DataFrame(edges).to_csv(out/'cross-sun-edges.csv',index=False)
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
