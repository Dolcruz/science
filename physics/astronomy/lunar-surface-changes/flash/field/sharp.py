from search import *
import argparse
P='M120012567LC';Q='M1428220502LC';T='M1471612432RC'

def candidate_input():
    parser = argparse.ArgumentParser(description="Select fine-resolution tiles from screened candidate coordinates.")
    parser.add_argument("table", nargs="?", type=Path, default=ROOT / "candidates.csv",
                        help="Candidate CSV with x and y in metres (default: field/search.py output).")
    return parser.parse_args().table

def run(table):
    scan.GRID=.7
    df=pd.read_csv(table)
    df['i']=np.floor(df.x/(.7*scan.CORE)).astype(int);df['j']=np.floor(df.y/(.7*scan.CORE)).astype(int)
    # Subpixel image comparison for screened sites on the 2010 left detector.
    from shapely.geometry import Point
    footprint=Polygon(((np.array(META[P]['corners'])-ORIGIN)*scan.SCALE)[[0,1,3,2]]).buffer(180)
    ds=df[[footprint.covers(Point(s.x,s.y)) for _,s in df.iterrows()]]
    keys=list(ds.groupby(['i','j']).groups)
    frames={k:frame(k,keys) for k in [P,Q,T,AFTER]}
    out=ROOT/'sharp';out.mkdir(exist_ok=True);stats=[]
    for (i,j),ss in ds.groupby(['i','j']):
        fixed=frames[AFTER].tile(i,j);ref_desc=scan.describe(fixed);reg={AFTER:fixed}
        for k in [P,Q,T]:
            z=scan.align(frames[k].tile(i,j),fixed,ref_desc)
            if z is not None:
                reg[k]=z[0];stats.append(dict(i=i,j=j,epoch=k,**z[1]))
        for _,s in ss.iterrows():
            x=round(scan.PAD+s.x/.7-i*scan.CORE);y=round(scan.PAD+s.y/.7-j*scan.CORE)
            chips={k:a[y-50:y+51,x-50:x+51] for k,a in reg.items() if np.min(a[y-22:y+23,x-22:x+23])>100}
            if P in chips and len(chips)>2:np.savez_compressed(out/(s['name']+'.npz'),**chips)
        (out/'stats.json').write_text(json.dumps(stats,indent=2))
        print(i,j,len(list(out.glob('*.npz'))),flush=True)
if __name__=='__main__':run(candidate_input())
