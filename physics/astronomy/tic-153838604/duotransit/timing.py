"""Empirical timing errors and a future photometric prediction for TIC 153838604."""
import argparse
import csv
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.constants import c
from astropy.coordinates import SkyCoord, get_body_barycentric
from astropy.time import Time
from scipy.stats import t as student

from measure import DURATION, fit_event, read_sector, triangular_profile


def geocentric_utc(btjd):
    target = SkyCoord(ra=68.073987*u.deg, dec=-47.608987*u.deg).cartesian
    arrival = Time(2457000 + btjd,format="jd",scale="tdb")
    # BJD_TDB = geocentric JD_TDB + light-time projection along this sight line.
    estimate = arrival
    for _ in range(2):
        offset = get_body_barycentric("earth",estimate).dot(target) / c
        estimate = arrival - offset.to(u.day)
    return estimate.utc.iso


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("fits"))
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    with (args.output/"measurements.csv").open(encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    errors = []
    timing = []
    for r in records:
        sector=int(r["sector"])
        time, flux, _, exposure, _, _ = read_sector(sector,args.cache)
        mid=float(r["fitted_btjd"]); depth=float(r["model_depth_ppt"])/1000
        width=float(r["model_duration_h"])/48
        shifts=[]
        # Nonoverlapping 0.60-day windows; one synthetic event per usable window.
        for centre in np.arange(time[0]+.30,time[-1]-.30,.60):
            if abs(centre-mid)<.60:continue
            keep=abs(time-centre)<.30
            x=time[keep];y=flux[keep]
            if len(x)<.72*.60/exposure:continue
            inner=abs(x-centre)<DURATION/2
            if np.sum(inner)<.72*DURATION/exposure:continue
            simulated=y - np.median(y)*depth*triangular_profile(x-centre,width,exposure)
            recovered=fit_event(x,simulated,centre,exposure)[0]
            shifts.append(recovered-centre)
        rms=float(np.sqrt(np.mean(np.square(shifts))))
        errors.append(rms)
        timing.append(dict(sector=sector,n_injections=len(shifts),rms_timing_min=rms*1440,
                           median_offset_min=np.median(shifts)*1440))
    with (args.output/"timing_controls.csv").open("w", newline="",encoding="utf-8") as out:
        w=csv.DictWriter(out,fieldnames=timing[0]);w.writeheader();w.writerows(timing)
    cycles=np.array([float(r["cycle"]) for r in records])
    measured=np.array([float(r["fitted_btjd"]) for r in records])
    X=np.column_stack([np.ones(len(records)),cycles])
    K=np.linalg.inv(X.T@X)@X.T
    intercept,period=K@measured
    covariance_empirical=K@np.diag(np.square(errors))@K.T
    residuals=measured-X@[intercept,period]
    dof=len(records)-2
    dispersion=np.sqrt(np.sum(residuals**2)/dof)
    covariance_fit=dispersion**2*np.linalg.inv(X.T@X)
    # Two independent estimates of uncertainty; retain the larger value for each statistic.
    period_se=max(np.sqrt(covariance_fit[1,1]),np.sqrt(covariance_empirical[1,1]))
    x=np.array([1.,53.])
    centre=float(x@[intercept,period])
    # Include event-to-event scatter as well as uncertainty in the fitted mean ephemeris.
    prediction_se=np.sqrt(max(x@covariance_fit@x,x@covariance_empirical@x)+dispersion**2)
    factor=student.ppf(.975,dof)
    print(timing)
    print(f"Period {period:.8f} d; 1-sigma scale {period_se:.7f} d; "
          f"conservative t(2) half width {factor*period_se:.7f} d")
    print(f"Cycle 53 midpoint {centre:.7f} BTJD, geocentric UTC {geocentric_utc(centre)}, "
          f"95% timing allowance {factor*prediction_se*1440:.2f} min.")
    print(f"Geocentric UTC including ±1.5 h for event and 30 min baseline on each side: "
          f"{geocentric_utc(centre-2/24-factor*prediction_se)} — "
          f"{geocentric_utc(centre+2/24+factor*prediction_se)}")

if __name__ == "__main__":
    main()
