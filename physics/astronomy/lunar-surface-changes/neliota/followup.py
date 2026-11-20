"""Extract and independently register dated terrain around a selected detector peak."""
import argparse,json,re
from pathlib import Path
import numpy as np, cv2, pandas as pd,requests
from shapely.geometry import Polygon,Point
from threadpoolctl import threadpool_limits
import registration as reg
from search import setup

class RemoteRows:
    def __init__(self, url, samples, folder):
        self.url, self.w, self.folder = url, samples, folder
        self.folder.mkdir(exist_ok=True,parents=True)
        label=self.read(0,8191)
        def number(key):
            return int(re.search(rb"^\s*"+re.escape(key)+rb"\s*=\s*(\d+)",label,re.M).group(1))
        self.offset=(number(b"^IMAGE")-1)*number(b"RECORD_BYTES")

    def read(self, start, end):
        name=self.url.rsplit("/",1)[-1]
        path=self.folder/f"{name}_{start}_{end}"
        if not path.exists():
            response=requests.get(self.url,headers={"Range":f"bytes={start}-{end}"})
            response.raise_for_status()
            if not response.headers.get("Content-Range","").startswith(f"bytes {start}-{end}/"):
                raise ValueError(f"Unexpected range response for {name}")
            if len(response.content)!=end-start+1: raise ValueError("Short response")
            path.write_bytes(response.content)
        return path.read_bytes()

    def __getitem__(self, key):
        ys,xs=key
        data=self.read(self.offset+2*self.w*ys.start,self.offset+2*self.w*ys.stop-1)
        return np.frombuffer(data,dtype="<i2").reshape(-1,self.w)[:,xs]


def frame(name, raw, info):
    if (raw/(name+".IMG")).is_file():
        reg.META[name]=info
        return reg.Frame(name,raw)
    f=reg.Frame.__new__(reg.Frame)
    f.name=name;f.h,f.w=info["lines"],info["samples"]
    f.vertices=(np.array(info["corners"])-reg.ORIGIN)*reg.SCALE/reg.GRID
    f.footprint=Polygon(f.vertices[[0,1,3,2]])
    f.image=RemoteRows(info["original"],f.w,raw/"ranges")
    return f


def extract(field,archive,x,y,raw,out):
    setup(field)
    ref=field['after'];allm={**archive,**field['observations']}
    lon,lat=reg.ORIGIN+np.array([x,y])*reg.GRID/reg.SCALE
    center=Point(lon,lat)
    i,j=x//reg.CORE,y//reg.CORE
    xx=x-i*reg.CORE+reg.PAD;yy=y-j*reg.CORE+reg.PAD
    region=np.s_[yy-40:yy+41,xx-40:xx+41]
    dest=frame(ref,raw,allm[ref]).tile(i,j);desc=reg.describe(dest)
    chips={};log=[]
    dy,dx=np.indices((81,81))-40;disk=dx**2+dy**2<=2.5**2
    ann=(dx**2+dy**2>=7**2)&(dx**2+dy**2<=15**2)
    for name,o in sorted(allm.items(),key=lambda kv:kv[1]['date']):
        if not Polygon(np.array(o['corners'])[[0,1,3,2]]).buffer(.004).covers(center):continue
        delta=abs((allm[ref]['bearing']-o['bearing']+180)%360-180)
        if delta>20:continue
        if name==ref:a=dest;st={}
        else:
            obj=frame(name,raw,o)
            tile=obj.tile(i,j);aligned=reg.align(tile,dest,desc)
            if aligned is None:
                log.append(dict(name=name,date=o['date'],status='unregistered'));continue
            a,st=aligned
        a=a[region]
        if a.shape!=(81,81) or (a[ann]<=100).any() or (a[disk]<=100).any():
            log.append(dict(name=name,date=o['date'],status='outside valid area'));continue
        chips[name]=a
        log.append(dict(name=name,date=o['date'],status='aligned',incidence=o['incidence_deg'],bearing=o['bearing'],
                        emission=o['emission'],local_log_contrast=np.log(a[disk]).mean()-np.median(np.log(a[ann])),**st))
    out.mkdir(exist_ok=True,parents=True)
    pd.DataFrame(log).to_csv(out/'dates.csv',index=False)
    np.savez_compressed(out/'chips.npz',**chips)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('field',type=Path);p.add_argument('archive',type=Path)
    p.add_argument('x',type=int);p.add_argument('y',type=int);p.add_argument('raw',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args()
    with threadpool_limits(4,'blas'):extract(json.loads(a.field.read_text()),json.loads(a.archive.read_text()),a.x,a.y,a.raw,a.out)
