"""Derive registered, quantitative before/after cutouts for all survey peaks."""
from survey import setup, scan, B, A
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def extract(raw, tables, out):
    setup()
    p = pd.read_csv(tables / (B+"-peaks.csv")).sort_values("z", ascending=False)
    out.mkdir(exist_ok=True, parents=True)
    frames = [scan.Frame(name, raw) for name in (B,A)]
    cutouts = {}
    for (i,j), group in p.groupby(["i","j"]):
        a,b = [f.tile(i,j) for f in frames]
        a,stats = scan.align(a,b,scan.describe(b))
        valid,layers = scan.scores(a,b)
        for row in group.itertuples():
            xx = int(row.x-i*scan.CORE+scan.PAD)
            yy = int(row.y-j*scan.CORE+scan.PAD)
            sl = np.s_[yy-40:yy+41,xx-40:xx+41]
            cutouts[f"{row.x}_{row.y}"] = np.stack([a[sl], b[sl], layers[0][1][sl]])
    np.savez_compressed(out/"peaks.npz", **cutouts)
    for n in range(0,len(p),24):
        fig,axes=plt.subplots(8,3,figsize=(13.2,15))
        for ax,row in zip(axes.ravel(),p.iloc[n:n+24].itertuples()):
            a,b,h = cutouts[f"{row.x}_{row.y}"]
            def norm(img):
                q=np.percentile(img,[1,98.5])
                return np.clip((img-q[0])/max(1,q[1]-q[0]),0,1)
            ax.imshow(np.hstack([norm(a),norm(b),np.clip(.5+h/0.13,0,1)]),cmap="gray",vmin=0,vmax=1)
            ax.set_title(f"x {row.x}, y {row.y}   z {row.z:.1f}",size=8)
        for ax in axes.ravel():ax.set_axis_off()
        fig.tight_layout(pad=.55);fig.savefig(out/f"gallery-{n//24+1}.jpg",dpi=100);plt.close(fig)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ["raw","tables","out"]: parser.add_argument(key,type=Path)
    args=parser.parse_args();extract(args.raw,args.tables,args.out)
