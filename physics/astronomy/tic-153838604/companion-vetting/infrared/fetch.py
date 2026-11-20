"""Download source exposures and the nearby AllWISE source list from IRSA."""
from pathlib import Path
import requests
import pandas as pd
from astropy.table import Table
from astropy import units as u
from astropy.coordinates import SkyCoord

HERE = Path(__file__).resolve().parent
RA, DEC = 68.07398832, -47.60899384
GATOR = "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query"
shared = ["ra","dec","mjd","nb","na","cc_flags","moon_masked","qi_fact","saa_sep"]
bands = [b+k for b in ["w1","w2"] for k in ["mpro","sigmpro","rchi2"]]
extra = ["w1frtr","w2frtr","w1sat","w2sat","qual_frame","ph_qual"]


def fetch(table,columns,radius):
    params = {"spatial":"Cone","catalog":table,"objstr":f"{RA} {DEC}","radius":radius,
              "radunits":"arcsec","outfmt":"1","selcols":",".join(columns),"outrows":0}
    r = requests.get(GATOR,params=params)
    r.raise_for_status()
    return Table.read(r.text.splitlines(),format="ascii.ipac").to_pandas()


def assemble(neo,old,neighbors):
    neo = neo.copy(); old = old.copy()
    neo["catalog"] = "NEOWISE"
    neo["frame"] = neo.scan_id+"-"+neo.frame_num.astype(str).str.zfill(3)
    old["catalog"] = "AllWISE"
    old = old.rename(columns={**{b+"_ep":b for b in bands},"frame_id":"frame"})
    cols = ["catalog","frame",*shared,*bands,*extra]
    out = pd.concat([old,neo],ignore_index=True).sort_values("mjd")
    assert not out.duplicated(["catalog","frame"]).any()
    out[cols].to_csv(HERE/"exposures.csv",index=False)
    neighbors = neighbors.copy()
    pos = SkyCoord(neighbors.ra.to_numpy()*u.deg,neighbors.dec.to_numpy()*u.deg)
    neighbors["separation_arcsec"] = pos.separation(SkyCoord(RA*u.deg,DEC*u.deg)).arcsec
    neighbor_cols = ["designation","ra","dec","separation_arcsec","w1mpro","w2mpro","ext_flg","cc_flags"]
    neighbors.sort_values("separation_arcsec")[neighbor_cols].to_csv(HERE/"neighbors.csv",index=False)


if __name__ == "__main__":
    neo = fetch("neowiser_p1bs_psd",["scan_id","frame_num",*shared,*bands,*extra],3)
    old = fetch("allwise_p3as_mep",["frame_id",*shared,*(b+"_ep" for b in bands)],3)
    neighbors = fetch("allwise_p3as_psd",["designation","ra","dec","w1mpro","w2mpro","ext_flg","cc_flags"],60)
    assemble(neo,old,neighbors)
