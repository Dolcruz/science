"""Forced ASAS-SN photometry at the TESS ephemeris, with matched control nights."""
import base64
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from astropy import constants as c, units as u
from astropy.coordinates import SkyCoord, get_body_barycentric
from astropy.time import Time

HERE = Path(__file__).resolve().parent
RA, DEC = 68.07396, -47.6088
GAIA = 4788303839668784896
TARGET = SkyCoord(RA*u.deg, DEC*u.deg)
P = 56.0793594
TIMINGS = pd.read_csv(HERE.parent.parent/"duotransit/measurements.csv")
T0 = 2457000 + np.polyfit(TIMINGS.cycle, TIMINGS.fitted_btjd, 1)[1]
HALF = 1.25/24


def fetch():
    radius, cat = 3/3600, "stellar_main"
    cols = ["asas_sn_id", "ra_deg", "dec_deg", "gaia_id"]
    server = "http://asassn-lb01.ifa.hawaii.edu:9006"
    rr = requests.post(f"{server}/lookup_cone/radius{radius}_ra{RA}_dec{DEC}",
                       json=dict(catalog=cat, cols=cols, format="arrow", download=True))
    rr.raise_for_status()
    (HERE/"index.parquet").write_bytes(rr.content)
    key = base64.encodebytes(f"conectr-{radius}_conera-{RA}_conedec-{DEC}|catalog-{cat}|cols-{'/'.join(cols)}".encode()).decode()
    servers = requests.get(server+"/get_block_servers").json()
    rr = requests.get(f"http://{servers[0]}:9006/get_block/query_hash-{key}-block_idx-0-catalog-{cat}")
    rr.raise_for_status()
    (HERE/"lightcurve.parquet").write_bytes(rr.content)


def offsets(t, phase):
    return (t - T0 + (.5-phase)*P) % P - P/2


def crosscheck_clock(table):
    legacy = HERE/"asas-v-legacy.csv"
    if not legacy.exists():
        r = requests.get("https://asas-sn.osu.edu/photometry/e58fabb7-bc30-58ce-b45f-424097ef0a3f.csv")
        r.raise_for_status()
        legacy.write_bytes(r.content)
    h = pd.read_csv(legacy).hjd.values
    x = table.loc[table.camera=="be","jd"].to_numpy()
    idx = abs(x[:,None]-h).argmin(axis=1)
    delta = (h[idx]-x)*86400
    match = abs(delta)<900
    t = Time(x,format="jd",scale="utc")
    correction = (TARGET.cartesian.xyz.value @ (get_body_barycentric("earth",t).xyz-get_body_barycentric("sun",t).xyz)/c.c).to_value(u.s)
    return dict(matched_camera_exposures=int(match.sum()), raw_median_abs_seconds=np.median(abs(delta[match])),
                corrected_median_abs_seconds=np.median(abs((delta-correction)[match])),
                legacy_primary_points=int(sum(abs(offsets(h,0))<HALF)),legacy_half_phase_points=int(sum(abs(offsets(h,.5))<HALF)))


def exact_controls(parts, observed):
    # A Cartesian product of empirical single-night controls, split in two
    # so the cumulative distribution can be evaluated without a huge matrix.
    midpoint = len(parts)//2
    sums = [np.sort([sum(t) for t in itertools.product(*group)])
            for group in (parts[:midpoint], parts[midpoint:])]
    a, b = sums
    def cdf(x):
        return np.searchsorted(b, x-a, side="right").sum()/(len(a)*len(b))
    def quantile(q):
        low,high = a[0]+b[0],a[-1]+b[-1]
        while high-low > 1e-8:
            mid = (high+low)/2
            if cdf(mid)<q:
                low=mid
            else:
                high=mid
        return (low+high)/2
    return 1-cdf(observed), observed-quantile(.975), observed-quantile(.025)


def analyze(d, phase, window):
    dt = offsets(d.t, phase)
    events = d.loc[abs(dt)<HALF].copy()
    events["delta_hours"] = dt.loc[events.index]*24
    rows, control, weights, scores = [], [], [], []
    for row in events.itertuples():
        dist = d.t-row.t
        use = (d.camera==row.camera) & (abs(dist)>.5) & (abs(dist)<=window)
        for ph in (0,.5):
            use &= abs(offsets(d.t,ph))>.08
        night = np.floor(dist[use]+.5)
        sample = d.loc[use].groupby(night).flux.median().to_numpy()
        mid = np.median(sample)
        deficits = 1000*(1 - sample/mid)
        sigma = 1.4826*np.median(abs(deficits-np.median(deficits)))
        deficit = 1000*(1-row.flux/mid)
        shape = 1-abs(row.delta_hours)/1.25
        rows.append(dict(phase=phase, camera=row.camera, jd=row.jd, offset_hours=row.delta_hours, profile=shape,
                         deficit_ppt=deficit, control_nights=len(sample), control_mad_ppt=sigma))
        control.append(deficits)
        weights.append(shape/sigma**2)
        scores.append(deficit)
    weights = np.array(weights)/sum(w*r["profile"] for w,r in zip(weights,rows))
    observed = np.dot(weights, scores)
    prob, low, high = exact_controls([w*c for w,c in zip(weights,control)], observed)
    return dict(phase=phase,window_days=window,points=len(rows),depth_ppt=observed,lower95_ppt=low,upper95_ppt=high,
                one_sided_control_tail=prob),rows


def main():
    if not (HERE/"lightcurve.parquet").exists():
        fetch()
    index = pd.read_parquet(HERE/"index.parquet")
    assert len(index)==1 and index.gaia_id.iloc[0]==GAIA
    table = pd.read_parquet(HERE/"lightcurve.parquet")
    assert set(table.asas_sn_id)==set(index.asas_sn_id)
    print("Timing check with legacy V photometry",crosscheck_clock(table))
    d = table.loc[(table.quality=="G") & (table.flux>0)].copy()
    clock = Time(d.jd.values,format="jd",scale="utc")
    direction = TARGET.cartesian.xyz.value
    results=[]
    # Sky Patrol v2 labels times 'jd'. Bracket conventions, including legacy HJD.
    for label,correction in [("JD as given",0),("UTC JD","earth"),("UTC HJD","sun")]:
        d["t"] = (d.jd if correction==0 else clock.tdb.jd +
                  (direction @ get_body_barycentric(correction,clock).xyz / c.c).to_value(u.day))
        for w in (14,30,60):
            for ph in (0,.5):
                summary, samples = analyze(d,ph,w)
                results.append(dict(time_convention=label,**summary))
                if w==30 and label=="UTC JD":
                    pd.DataFrame(samples).to_csv(HERE/f"phase-{ph}-measurements.csv",index=False)
    pd.DataFrame(results).to_csv(HERE/"depths.csv",index=False)
    print("All / accepted",len(table),len(d),"T0",T0)
    print(pd.DataFrame(results).round(3).to_string(index=False))


if __name__=="__main__":
    main()
