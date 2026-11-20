"""Retrieve independent NAC tiles and align them on terrain around a survey peak."""
import argparse
from pathlib import Path
import json

from survey import setup, scan, B, A
from lines import Lines
import numpy as np
from shapely.geometry import Polygon,Point


def build_frame(name, raw):
    if (raw/(name+".IMG")).exists():
        return scan.Frame(name,raw)
    result=scan.Frame.__new__(scan.Frame)
    m=scan.META[name]
    result.name=name
    result.vertices=(np.asarray(m["corners"])-scan.ORIGIN)*scan.SCALE/scan.GRID
    result.footprint=Polygon(result.vertices[[0,1,3,2]])
    result.h,result.w=m["lines"],m["samples"]
    result.image=Lines(m,raw/"ranges")
    return result

def collect(raw, meta, out, x, y, names):
    setup()
    scan.META=json.loads(meta.read_text())
    i,j=x//scan.CORE,y//scan.CORE
    cx=x-i*scan.CORE+scan.PAD
    cy=y-j*scan.CORE+scan.PAD
    out.mkdir(exist_ok=True,parents=True)
    ref=build_frame(A,raw);b=ref.tile(i,j)
    desc=scan.describe(b)
    sl=np.s_[cy-96:cy+97,cx-96:cx+97]
    imgs={A:b[sl]}
    records={}
    for name in names:
        if name==A:continue
        f=build_frame(name,raw)
        if not f.footprint.buffer(250).contains(Point(x,y)):continue
        a=f.tile(i,j)
        reg=scan.align(a,b,desc)
        if reg is None:
            records[name]={"aligned":False};continue
        a,stats=reg
        records[name]=dict(aligned=True,**stats,valid=int((a[sl]>100).sum()))
        if (a[sl]>100).all(): imgs[name]=a[sl]
        print(name,records[name],flush=True)
    np.savez_compressed(out/f"site-{x}-{y}.npz",**imgs)
    (out/f"registration-{x}-{y}.json").write_text(json.dumps(records,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for k in ["raw","meta","out"]:p.add_argument(k,type=Path)
    for k in ["x","y"]:p.add_argument(k,type=int)
    p.add_argument("names",nargs="+")
    q=p.parse_args();collect(q.raw,q.meta,q.out,q.x,q.y,q.names)
