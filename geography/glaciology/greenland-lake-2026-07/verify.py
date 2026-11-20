"""Check reported areas and radar fractions from the distributed science pixels."""
import csv
from pathlib import Path
import numpy as np
from scipy import ndimage as nd

ROOT=Path(__file__).resolve().parent


def main():
    with (ROOT/"optical.csv").open() as stream:
        optical={r["id"]:r for r in csv.DictReader(stream)}
    with (ROOT/"radar.csv").open() as stream:
        radar={r["id"]:r for r in csv.DictReader(stream)}
    count=0
    with np.load(ROOT/"measurement-chips.npz") as chips:
        for name in chips:
            if name.endswith("_blue"):
                ident=name[:-5];is_s2=ident.startswith("S2")
                scale,offset,px=(.0001,-.1,10) if is_s2 else (.0000275,-.2,30)
                b=chips[name].astype(float);r=chips[ident+"_red"].astype(float)
                valid=(b>0)&(r>0)
                if is_s2:valid&=~np.isin(chips[ident+"_scl"],[0,3,8,9,10])
                else:valid&=(chips[ident+"_qa_pixel"]&31)==0
                idx=(b-r)*scale/((b+r)*scale+2*offset+.0001)
                for threshold in [.20,.25,.30]:
                    area=np.sum(valid&(idx>threshold))*px**2/1e6
                    np.testing.assert_allclose(area,float(optical[ident][f"water_km2_{threshold:.2f}"]),atol=1.e-8)
                    count+=1
            elif name.endswith("_hh"):
                ident=name[:-3];a=chips[name];good=a>0
                coverage=nd.uniform_filter(good.astype(float),5)>.99999
                smooth=nd.uniform_filter(np.where(good,a,0.).astype(float),5)
                z=10*np.log10(np.maximum(smooth,1e-10));s=coverage&good
                z-=np.median(z[s&chips["radar_dry"]])
                for n in [3,4.5,6]:
                    frac=np.mean(z[s&chips["radar_foot"]]<-n)
                    np.testing.assert_allclose(frac,float(radar[ident][f"foot_below_{n:g}dB"]),atol=1e-8)
                    count+=1
    print(f"Verified {count} optical areas and radar fractions from archived pixel cutouts.")


if __name__=="__main__":
    main()
