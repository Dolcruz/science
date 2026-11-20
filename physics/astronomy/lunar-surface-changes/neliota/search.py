"""Search a matched full pair and preserve the native pixels and scores of each flag."""
from pathlib import Path
import argparse,math,json
import cv2,numpy as np,pandas as pd,requests
from shapely.geometry import box
from threadpoolctl import threadpool_limits
import registration as reg
from checksums import verify

def setup(field):
    reg.META=field["observations"]
    reg.GRID=field['grid_m']
    reg.ORIGIN=np.array([field["lon"],field["lat"]])
    reg.SCALE=np.array([reg.DEG*math.cos(math.radians(field['lat'])),-reg.DEG])

def fetch_one(folder,name,meta):
    folder.mkdir(exist_ok=True,parents=True)
    dest=folder/(name+'.IMG')
    if not dest.is_file():
        tmp=dest.with_suffix('.part')
        with requests.get(meta['original'],stream=True) as r:
            r.raise_for_status()
            with tmp.open('wb') as f:
                for chunk in r.iter_content(2**20): f.write(chunk)
        verify(tmp);tmp.replace(dest)
    print(name,verify(dest),flush=True)

def scan(field,raw,out):
    setup(field)
    out.mkdir(exist_ok=True,parents=True)
    for n in (field['before'],field['after']):fetch_one(raw,n,reg.META[n])
    a,b=(reg.Frame(n,raw) for n in (field['before'],field['after']))
    overlap=a.footprint.intersection(b.footprint)
    c,p=reg.CORE,reg.PAD
    x0,y0,x1,y1=overlap.bounds
    tiles=[(i,j) for j in range(math.floor(y0/c)-1,math.ceil(y1/c)+1) for i in range(math.floor(x0/c)-1,math.ceil(x1/c)+1)
           if overlap.buffer(p).intersects(box(i*c,j*c,(i+1)*c,(j+1)*c))]
    peaks=[];cuts={};masks={};counts=[]
    inner=np.s_[p:p+c,p:p+c]
    xlocal,ylocal=np.meshgrid(np.arange(c),np.arange(c))
    for k,(i,j) in enumerate(tiles):
        aa,bb=a.tile(i,j),b.tile(i,j)
        result=reg.align(aa,bb,reg.describe(bb))
        row=dict(i=i,j=j,valid=0,in_prediction_box=0)
        if result is not None:
            aa,st=result
            valid,layers=reg.scores(aa,bb)
            core=valid[inner];masks[f'{i}_{j}']=np.packbits(core)
            inbox=(abs((i*c+xlocal)*reg.GRID/reg.SCALE[0])<=.5)&(abs((j*c+ylocal)*reg.GRID/reg.SCALE[1])<=.5)
            row.update(st,valid=int(core.sum()),in_prediction_box=int(np.count_nonzero(core&inbox)))
            for sigma,layer,z in layers:
                for sign in [1,-1]:
                    amp=layer*sign
                    pick=valid&(amp>=cv2.dilate(amp,np.ones((21,21),'u1')))&(amp>=.035)&(sign*z>=3.5)
                    for yy,xx in zip(*np.where(pick[inner])):
                        x=int(i*c+xx);y=int(j*c+yy);u=xx+p;v=yy+p
                        sample,line=b.native(x,y);lon,lat=reg.ORIGIN+np.array([x,y])*reg.GRID/reg.SCALE
                        key=f'{x}_{y}';ch=np.s_[v-32:v+33,u-32:u+33]
                        cuts[key]=np.stack((aa[ch],bb[ch])).astype('float32')
                        peaks.append(dict(x=x,y=y,sigma=sigma,sign=sign,amplitude=float(layer[v,u]),score=float(sign*z[v,u]),
                                          lon=lon,lat=lat,sample0=float(sample),line0=float(line),in_box=inbox[yy,xx],chip=key))
        counts.append(row)
        if k%30==0:print(k+1,len(tiles),round(sum(r['valid'] for r in counts)*reg.GRID**2/1e6,2),'km2',len(peaks),'flags',flush=True)
    pd.DataFrame(peaks,columns='x y sigma sign amplitude score lon lat sample0 line0 in_box chip'.split()).to_csv(out/'peaks.csv',index=False)
    pd.DataFrame(counts).to_csv(out/'tiles.csv',index=False)
    np.savez_compressed(out/'masks.npz',**masks);np.savez_compressed(out/'cutouts.npz',**cuts)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('field',type=Path);p.add_argument('raw',type=Path);p.add_argument('out',type=Path)
    args=p.parse_args()
    with threadpool_limits(limits=4,user_api='blas'):
        scan(json.loads(args.field.read_text()),args.raw,args.out)
