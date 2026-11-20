"""Interpolate each oblique view from surrounding terrain, excluding the change site."""
from survey import setup,scan,A,B
import cv2
import numpy as np
import pandas as pd
from itertools import combinations
from pathlib import Path
import json,sys
setup()
C=np.array([864.,471.]) # grid x=2432,y=10103 in tile (2,11) plus padding

def features(raw, mode="band"):
    valid=raw>100
    v=np.log(np.maximum(100,raw))
    hi=cv2.GaussianBlur(v,(0,0),1)-cv2.GaussianBlur(v,(0,0),14)
    n=np.maximum(.007,cv2.GaussianBlur(abs(hi),(0,0),24))
    band=np.uint8(np.clip(127+47*hi/n,0,255))
    if mode=="negative":band=255-band
    if mode=="gradient":
        gx=cv2.Sobel(hi,cv2.CV_32F,1,0);gy=cv2.Sobel(hi,cv2.CV_32F,0,1)
        mag=cv2.magnitude(gx,gy)
        band=np.uint8(np.clip(63*mag/np.maximum(.004,cv2.GaussianBlur(mag,(0,0),18)),0,255))
    mask=cv2.erode(np.uint8(valid)*255,np.ones((31,31),np.uint8))
    kp,ds=cv2.SIFT_create().detectAndCompute(band,mask)
    return np.float32([k.pt for k in kp]),ds

def match(f,g,p):
    x,df=f;y,dg=g
    if df is None or dg is None:return
    knn=cv2.FlannBasedMatcher(dict(algorithm=1,trees=5),dict(checks=64)).knnMatch(df,dg,k=2)
    idx=np.array([(a.queryIdx,a.trainIdx) for a,b in knn if a.distance<.82*b.distance],int).reshape(-1,2)
    if len(idx)<5:return
    a=x[idx[:,0]];b=y[idx[:,1]]
    ok=np.linalg.norm(a-p,axis=1)>70
    a,b=a[ok],b[ok]
    m,inl=cv2.estimateAffine2D(a,b,ransacReprojThreshold=5,maxIters=10000,confidence=.999)
    if m is None or inl.sum()<12 or max(abs(np.linalg.svd(m[:,:2],compute_uv=False)-1))>.15 or np.linalg.det(m[:,:2])<=0:return
    k=inl.ravel().astype(bool);a,b=a[k],b[k]
    qa=np.rint(a).astype(int)
    ids=np.unique(qa,axis=0,return_index=True)[1];a,b=a[ids],b[ids]
    def pred(p,a,b):
        k=np.exp(-.5*(np.linalg.norm(a-p,axis=1)/200)**2)
        mat=np.column_stack([np.ones(len(a)),(a-p)/200]);delta=b-a
        w=k
        for _ in range(4):
            coef=np.linalg.lstsq(mat*np.sqrt(w[:,None]),delta*np.sqrt(w[:,None]),rcond=None)[0]
            w=k*np.minimum(1,1.5/np.maximum(.01,np.linalg.norm(mat@coef-delta,axis=1)))
        return p+coef[0]
    q=pred(p,a,b)
    d=np.linalg.norm(a-p,axis=1);near=(d<450)
    if (near).sum()<8:return
    # The same missing-neighborhood rule used at the investigation point.
    err=[]
    # Use one independent checkpoint in each occupied 64-pixel block.
    near_idx=np.where(near)[0]
    blocks=np.floor(a[near_idx]/64).astype(int)
    centers=(blocks+.5)*64
    ordered=near_idx[np.argsort(np.linalg.norm(a[near_idx]-centers,axis=1))]
    pick=np.unique(np.floor(a[ordered]/64),axis=0,return_index=True)[1]
    for h in ordered[pick]:
        k=np.linalg.norm(a-a[h],axis=1)>70
        if k.sum()>6:err.append(np.linalg.norm(pred(a[h],a[k],b[k])-b[h]))
    if len(err)<8:return
    return q,dict(n=len(a),near=int(near.sum()),nearest=float(d.min()),p50=float(np.median(err)),p90=float(np.quantile(err,.9)),checks=len(err))

def go(folder,out,names,resume=False):
    out.mkdir(exist_ok=True,parents=True)
    ims={n:np.load(folder/(n+'.npy')) for n in names}
    featureset={n:features(a) for n,a in ims.items()}
    paths={A:C}; records={};edges=[]
    if resume and (out/'projected-centers.npz').exists():
        paths=dict(np.load(out/'projected-centers.npz'))
        records=json.loads((out/'best-links.json').read_text())
        edges=pd.read_csv(out/'terrain-links.csv').to_dict('records')
    # The ordered anchor list runs from matched high-Sun images through intermediate to grazing incidence.
    for n in names[1:]:
        if n in paths:continue
        options=[]
        for f in list(paths):
            # Route costs accumulate with each tie transfer.
            if n==f:continue
            r=match(featureset[f],featureset[n],paths[f])
            if r is None:continue
            q,stats=r
            cost=stats['p90']+records.get(f,{}).get('cost',0)
            rec=dict(source=f,destination=n,qx=float(q[0]),qy=float(q[1]),cost=cost,**stats)
            edges.append(rec);options.append((cost,q,rec))
        if options:
            _,q,rec=min(options,key=lambda r:r[0]);paths[n]=q;records[n]=rec;print(n,rec,flush=True)
        else:print(n,'no terrain link',flush=True)
        np.savez_compressed(out/'projected-centers.npz',**paths)
        pd.DataFrame(edges).to_csv(out/'terrain-links.csv',index=False)
        (out/'best-links.json').write_text(json.dumps(records,indent=2))
    np.savez_compressed(out/'projected-centers.npz',**paths)
    pd.DataFrame(edges).to_csv(out/'terrain-links.csv',index=False)
    (out/'best-links.json').write_text(json.dumps(records,indent=2))

if __name__=="__main__":
    go(Path(sys.argv[1]),Path(sys.argv[2]),[n for n in sys.argv[3:] if n!='--resume'], '--resume' in sys.argv[3:])
