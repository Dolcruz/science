"""Retrieve calibrated NAC row ranges and search multiepoch lunar temporal pairs."""
import os
for var in ["OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","BLIS_NUM_THREADS","NUMEXPR_NUM_THREADS"]:
    os.environ[var]="4"
import json,re,sys
from pathlib import Path
import numpy as np, pandas as pd, cv2,requests
from shapely.geometry import Polygon
from scipy.ndimage import maximum_filter
ROOT=Path(__file__).resolve().parent
import scan
cv2.setNumThreads(4)
ORIGIN=np.array([335.6698,20.7135])
scan.GRID=1.0
scan.ORIGIN=ORIGIN
scan.SCALE=np.array([scan.DEG*np.cos(np.deg2rad(ORIGIN[1])),-scan.DEG])
META=json.loads((ROOT/'metadata.json').read_text())
# 2012/2022 western sunlight at moderate and high incidence, independent acquisitions.
BEFORE='M183689789LC';AFTER='M1415343880RC';EARLY='M1129645568LC'
HIB='M181330922LC';HIA='M1412996974RC';EAST='M1521927263LC';WEST='M1527807868RC'
PAIRS=[(BEFORE,AFTER),(BEFORE,EARLY),(HIB,HIA)]
SITE=ROOT/'ranges';SITE.mkdir(exist_ok=True)
tiles=[(i,j) for j in range(-5,5) for i in range(-2,2)]

def readbytes(u,lo,hi,path):
    if not path.exists():
        r=requests.get(u,headers={'Range':f'bytes={lo}-{hi}'});r.raise_for_status()
        assert r.headers['Content-Range'].startswith(f'bytes {lo}-{hi}/') and len(r.content)==hi-lo+1
        path.write_bytes(r.content)
    return path

class RowSubset:
    def __init__(self,a,start,stop,w):self.m=a;self.start=start;self.stop=stop;self.width=w
    def __getitem__(self,key):
        y,x=key
        assert y.start>=self.start and y.stop<=self.stop,(y,self.start,self.stop)
        return self.m[y.start-self.start:y.stop-self.start,x]

def frame(id,chosen_tiles=tiles):
    info=META[id]
    f=scan.Frame.__new__(scan.Frame);f.w=info['samples'];f.h=info['lines'];f.name=id
    f.vertices=(np.asarray(info['corners'])-ORIGIN)*scan.SCALE/scan.GRID
    f.footprint=Polygon(f.vertices[[0,1,3,2]])
    lo,hi=f.h,0
    for i,j in chosen_tiles:
        v=np.array([-scan.PAD-65,scan.CORE+scan.PAD+65])
        xx,yy=np.meshgrid(i*scan.CORE+v,j*scan.CORE+v)
        _,row=f.native(xx,yy)
        lo=min(lo,max(0,int(row.min())-4));hi=max(hi,min(f.h,int(row.max())+6))
    u=info['original'];head=readbytes(u,0,8191,SITE/(id+'.lbl')).read_bytes()
    key=lambda k:int(re.search(rb'^\s*'+re.escape(k)+rb'\s*=\s*(\d+)',head,re.M)[1])
    offset=(key(b'^IMAGE')-1)*key(b'RECORD_BYTES')
    for path in SITE.glob(id+'_*.rows'):
        _,left,right=path.stem.split('_')
        if int(left)<=lo and int(right)>=hi:
            lo,hi=int(left),int(right)
            break
    else:
        path=readbytes(u,offset+2*f.w*lo,offset+2*f.w*hi-1,SITE/f'{id}_{lo}_{hi}.rows')
    f.image=RowSubset(np.memmap(path,mode='r',dtype='<i2',shape=(hi-lo,f.w)),lo,hi,f.w)
    return f

def diff(a,b):
    val=cv2.erode(((a>100)&(b>100)).astype('u1'),np.ones((51,51),'u1')).astype(bool)
    aa=np.log(np.maximum(100,a));bb=np.log(np.maximum(100,b))
    g=lambda f,s:cv2.GaussianBlur(f,(0,0),s)
    raw=bb-aa
    d=raw-g(raw,18)
    sm=g(d,1.7)
    sn=sm/np.maximum(.007,1.25*g(abs(sm),24))
    return sm,sn,val

def run():
    frames={id:frame(id) for id in [AFTER,BEFORE,EARLY,HIB,HIA]}
    out=ROOT/'chips';out.mkdir(exist_ok=True)
    cand=[];census=[]
    pad=scan.PAD;size=scan.CORE; sl=np.s_[pad:pad+size,pad:pad+size]
    for i,j in tiles:
        ref=frames[AFTER].tile(i,j);desc=scan.describe(ref)
        im={AFTER:ref}
        for k in (BEFORE,EARLY,HIB,HIA):
            z=scan.align(frames[k].tile(i,j),ref,desc)
            if z is not None:im[k]=z[0]
        if BEFORE not in im:continue
        masks=[];ds=[];zs=[]
        for a,b in PAIRS:
            if a in im and b in im:
                d,z,mask=diff(im[a],im[b]);ds.append(d[sl]);zs.append(z[sl]);masks.append(mask[sl])
            else:ds.append(np.zeros((size,size),'f4'));zs.append(ds[-1]);masks.append(np.zeros((size,size),bool))
        pairnum=np.sum(masks,axis=0)
        census.append((i,j,*[int(k.sum()) for k in masks],int((pairnum==3).sum())))
        for sign in (-1,1):
            # Two date brackets must agree. Prefer disjoint image pairs where available.
            a0=sign*ds[0];z0=sign*zs[0]
            z1=np.where(masks[1],sign*zs[1],-np.inf);z2=np.where(masks[2],sign*zs[2],-np.inf)
            sc=np.minimum(z0,np.maximum(z1,z2))
            peaks=masks[0] & (pairnum>=2)&(a0>.028)&(sc>2.5)&(sc>=maximum_filter(sc,21))
            for yy,xx in np.column_stack(np.where(peaks)):
                x=int(i*size+xx);y=int(j*size+yy)
                if not (pad+yy-40>=0 and pad+xx-40>=0):continue
                win=np.s_[pad+yy-40:pad+yy+41,pad+xx-40:pad+xx+41]
                name=f'x{x}y{y}'
                np.savez_compressed(out/(name+'.npz'),**{k:im[k][win] for k in im})
                cand.append(dict(name=name,x=x,y=y,sign=sign,score=sc[yy,xx],moderate_d=ds[0][yy,xx],early_d=ds[1][yy,xx] if masks[1][yy,xx] else np.nan,
                                 high_d=ds[2][yy,xx] if masks[2][yy,xx] else np.nan,z0=z0[yy,xx],z1=z1[yy,xx],z2=z2[yy,xx]))
        print(i,j,len(cand),census[-1],flush=True)
    pd.DataFrame(census,columns=['i','j','moderate','early','high','all']).to_csv(ROOT/'coverage.csv',index=False)
    pd.DataFrame(cand).sort_values('score',ascending=False).to_csv(ROOT/'candidates.csv',index=False)

if __name__=='__main__':run()
