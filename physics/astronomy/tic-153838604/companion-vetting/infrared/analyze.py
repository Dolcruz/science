"""Fold native WISE and NEOWISE single-exposure photometry on the TESS ephemeris."""
from pathlib import Path
import numpy as np
import pandas as pd
from astropy import units as u
from astropy.constants import c
from astropy.coordinates import get_body_barycentric, SkyCoord
from astropy.time import Time

HERE = Path(__file__).resolve().parent
PERIOD = 56.0793594
T0 = 2458447.10503
DURATION_H = 2.61
TARGET = SkyCoord(68.07398832*u.deg, -47.60899384*u.deg)
FLAGS = {col:str for col in ["cc_flags","moon_masked","w1frtr","w2frtr","ph_qual"]}


def barycentric_dates(d):
    mjd = d.mjd.to_numpy().copy()
    early = (d.catalog == "NEOWISE") & (d.mjd < 57196.47882488)
    mjd[early] -= 1.57/86400
    t = Time(mjd, format="mjd", scale="utc")
    projection = (get_body_barycentric("earth",t).xyz*TARGET.cartesian.xyz[:,None]).sum(axis=0)
    return t.tdb.jd + (projection/c).to_value(u.day)


def annotate(d):
    d = d.sort_values("mjd").copy()
    d["bjd_tdb"] = barycentric_dates(d)
    d["date_utc"] = Time(d.mjd,format="mjd",scale="utc").isot
    elapsed = d.bjd_tdb - T0
    for tag,frac in [("primary",0),("half",0.5)]:
        d[tag+"_hours"] = ((elapsed-frac*PERIOD+PERIOD/2)%PERIOD-PERIOD/2)*24
    d["event"] = np.select([abs(d.primary_hours)<=DURATION_H/2, abs(d.half_hours)<=DURATION_H/2],
                           ["primary","halfway"], default="outside")
    # Annual survey passes are separated by >149 d in this dataset.
    d["visit"] = (d.mjd.diff()>30).cumsum()
    return d


def clean(d, band, strict):
    b = "w"+str(band)
    i = band-1
    keep = ((d.qi_fact == 1 if strict else d.qi_fact > 0) & (d.saa_sep > 0)
            & d.cc_flags.str[i].eq("0") & d.moon_masked.str[i].eq("0")
            & (d.nb == 1) & (d.na == 0) & (d[b+"sigmpro"] > 0) & d[b+"mpro"].notna())
    neowise = ((d.qual_frame > 0) & d.ph_qual.str[i].eq("A") & (d[b+"sat"] == 0)
               & d[b+"frtr"].eq("0000") & (d[b+"rchi2"] < 2))
    return keep & ((d.catalog == "AllWISE") | neowise)


def measurements(d):
    result = []
    # Guard the baseline by a full event duration around either test center.
    outside = (abs(d.primary_hours) > DURATION_H) & (abs(d.half_hours) > DURATION_H)
    for strict in [True,False]:
        for band in [1,2]:
            b = "w"+str(band)
            valid = clean(d,band,strict)
            for _,r in d[d.event != "outside"].iterrows():
                same = d[(d.visit==r.visit)&valid&outside]
                mag = same[b+"mpro"].to_numpy()
                baseline = np.median(mag)
                mad = 1.4826*np.median(np.abs(mag-baseline))
                # Formal median error assumes independent baseline errors. Also report observed scatter.
                base_se = 1.2533*mad/np.sqrt(len(same))
                res = r[b+"mpro"] - baseline
                sigma = np.hypot(r[b+"sigmpro"],base_se)
                loss = 1-10**(-.4*res)
                loss_err = .4*np.log(10)*(1-loss)*sigma
                result.append(dict(frame=r.frame,mjd=r.mjd,date_utc=r.date_utc,event=r.event,
                    hours=(r.primary_hours if r.event=="primary" else r.half_hours),band=b.upper(),
                    selection=("full frame quality" if strict else "positive frame quality"),
                    accepted=bool(valid.loc[r.name]),visit=r.visit,baseline_count=len(same),
                    baseline_mag=baseline,baseline_observed_scatter_mag=mad,
                    baseline_as_faint=int((mag>=r[b+"mpro"]).sum()),
                    mag=r[b+"mpro"],catalog_error_mag=r[b+"sigmpro"],residual_mag=res,
                    flux_loss_fraction=loss,formal_error_fraction=loss_err,
                    gaussian_upper95_loss_fraction=1-10**(-.4*(res+1.644854*sigma)),
                    frame_quality=r.qi_fact,transient_flag=r[b+"frtr"]))
    return pd.DataFrame(result)


def colors(d):
    valid = clean(d,1,True) & clean(d,2,True)
    outside = (abs(d.primary_hours) > DURATION_H) & (abs(d.half_hours) > DURATION_H)
    rows = []
    for _, r in d[(d.event!="outside")&valid].iterrows():
        baseline = d[(d.visit==r.visit)&outside&valid]
        values = (baseline.w1mpro-baseline.w2mpro).to_numpy()
        ref = np.median(values)
        spread = 1.4826*np.median(abs(values-ref))
        error = np.sqrt(r.w1sigmpro**2+r.w2sigmpro**2+(1.2533*spread/np.sqrt(len(values)))**2)
        rows.append(dict(frame=r.frame,event=r.event,date_utc=r.date_utc,
                         delta_w1_minus_w2_mag=r.w1mpro-r.w2mpro-ref,
                         formal_error_mag=error,baseline_mad_sigma_mag=spread,n_reference=len(values)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    d = annotate(pd.read_csv(HERE/"exposures.csv",dtype=FLAGS))
    out = measurements(d)
    out.to_csv(HERE/"eclipse_windows.csv",index=False)
    colors(d).to_csv(HERE/"colors.csv",index=False)
    print(d.groupby(["catalog","event"]).size())
    print(out[out.selection=="full frame quality"][["date_utc","event","hours","band","accepted","baseline_count",
          "baseline_observed_scatter_mag","flux_loss_fraction","formal_error_fraction"]].to_string(index=False))
    print("Closest AllWISE offsets in hours",d[d.catalog=="AllWISE"][["primary_hours","half_hours"]].abs().min().to_dict())
