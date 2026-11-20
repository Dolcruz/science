"""Same-image differential calibration of the four ASAS-SN primary epochs."""
import base64
import io

import numpy as np
import pandas as pd
import requests
from astropy import constants as c, units as u
from astropy.coordinates import get_body_barycentric
from astropy.time import Time

from analyze import HERE, RA, DEC, TARGET, analyze


def fetch_controls(folder, inner_arcmin, outer_deg):
    base = "http://asassn-lb01.ifa.hawaii.edu:9006"
    cat = "stellar_main"
    cols = ["asas_sn_id","ra_deg","dec_deg","gaia_mag","gaia_b_mag","gaia_r_mag"]
    r = requests.post(f"{base}/lookup_cone/radius{outer_deg}_ra{RA}_dec{DEC}",json=dict(catalog=cat,cols=cols,format="arrow",download=False))
    r.raise_for_status()
    field = pd.read_parquet(io.BytesIO(r.content)).dropna()
    separation = 60*np.hypot((field.ra_deg-RA)*np.cos(np.deg2rad(DEC)), field.dec_deg-DEC)
    color = field.gaia_b_mag-field.gaia_r_mag
    refs = field[(separation>inner_arcmin)&(abs(field.gaia_mag-12.9243)<.6)&(abs(color-.864)<.35)].copy()
    refs.to_csv(folder/"comparison-stars.csv",index=False)
    ids = sorted(map(int, refs.asas_sn_id))
    cols = ["asas_sn_id","ra_deg","dec_deg"]
    r = requests.post(base+"/lookup_targets/catalog_list",json=dict(tar_ids=ids,catalog=cat,id_col="asas_sn_id",cols=cols,format="arrow",download=True))
    r.raise_for_status()
    assert set(pd.read_parquet(io.BytesIO(r.content)).asas_sn_id)==set(ids)
    key = base64.encodebytes(f"listlen-{len(ids)}_listfirst-{ids[0]}_listend-{ids[-1]}|catalog-{cat}|id_col-asas_sn_id|cols-{'/'.join(cols)}".encode()).decode()
    hosts = requests.get(base+"/get_block_servers").json()
    r = requests.get(f"http://{hosts[0]}:9006/get_block/query_hash-{key}-block_idx-0-catalog-{cat}")
    r.raise_for_status()
    (folder/"comparison-stars.parquet").write_bytes(r.content)


def calibrate(folder, inner_arcmin, outer_deg):
    folder.mkdir(exist_ok=True)
    if not (folder/"comparison-stars.parquet").exists():
        fetch_controls(folder, inner_arcmin, outer_deg)
    refs = pd.read_parquet(folder/"comparison-stars.parquet").query("quality=='G' and flux>0").copy()
    refs = refs.sort_values("jd")
    refs["time"] = pd.to_datetime(refs.jd-2440587.5,unit="D")
    def relative(g):
        # Estimate each reference star's local level independently of the target.
        y=g.set_index("time").flux
        return (y/y.rolling("60D",center=True,min_periods=3).median()).values
    refs["relative_flux"]=np.nan
    for _,g in refs.groupby(["asas_sn_id","camera"]):
        refs.loc[g.index,"relative_flux"] = relative(g)
    ensemble = refs.groupby("image_id").relative_flux.agg(["median","count"])
    d = pd.read_parquet(HERE/"lightcurve.parquet").query("quality=='G' and flux>0").merge(ensemble,on="image_id")
    d = d.loc[d["count"]>=3].copy()
    d["flux"] /= d["median"]
    clock=Time(d.jd.values,format="jd",scale="utc")
    d["t"]=clock.tdb.jd+(TARGET.cartesian.xyz.value @ get_body_barycentric("earth",clock).xyz/c.c).to_value(u.day)
    d[["jd","t","flux","camera","image_id","count","median"]].to_csv(folder/"calibrated-target.csv",index=False)
    result=[]
    for w in (14,30,60):
        for ph in (0,.5):
            summary,rows=analyze(d,ph,w)
            result.append(summary)
            if w==30:
                pd.DataFrame(rows).merge(d[["jd","count","median"]],on="jd").to_csv(folder/f"differential-{ph}-events.csv",index=False)
    pd.DataFrame(result).to_csv(folder/"differential-depths.csv",index=False)
    print("comparison stars",refs.asas_sn_id.nunique(),"target exposures",len(d))
    print(pd.DataFrame(result).round(4).to_string(index=False))


if __name__=="__main__":
    calibrate(HERE,1,.25)
    calibrate(HERE/"outer-field",15,.50)
