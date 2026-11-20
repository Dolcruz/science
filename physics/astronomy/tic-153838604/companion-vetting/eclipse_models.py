"""Fit fixed-radius occultations to the four public QLP light curves.

Requires numpy, scipy, astropy, matplotlib, and batman-package.
Run alongside the sibling duotransit data directory.
"""
import csv
import json
from pathlib import Path

import numpy as np
import batman
from astropy import constants as c, units as u
from astropy.io import fits
from batman import _quadratic_ld
from matplotlib import pyplot as plt
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "duotransit"
RS = 0.906468 * c.R_sun
MS = c.M_sun
PERIOD = 56.0793594 * u.day
NODES, WEIGHTS = np.polynomial.legendre.leggauss(12)
WEIGHTS /= 2


def datasets():
    events = []
    for row in csv.DictReader((INPUT / "measurements.csv").open()):
        sector = int(row["sector"])
        path, = (INPUT / "fits").glob(f"*s{sector:04d}-*.fits")
        with fits.open(path) as hd:
            data = hd[1].data
            exposure = hd[1].header["TIMEDEL"]
            t = data["TIME"] - float(row["fitted_btjd"])
            y = data["DET_FLUX" if "DET_FLUX" in data.names else "KSPSAP_FLUX"]
            keep = (data["QUALITY"] == 0) & np.isfinite(y) & (abs(t) < .30)
            x, y = np.array(t[keep], float), np.array(y[keep], float)
        baseline = abs(x) > .08
        y = y / np.median(y[baseline]) - 1
        design = np.column_stack([np.ones(len(x)), x])
        resid = y[baseline] - design[baseline] @ np.linalg.lstsq(design[baseline], y[baseline], rcond=None)[0]
        rms = 1.4826 * np.median(abs(resid - np.median(resid)))
        events.append((sector, x, y, x[:, None] + exposure / 2 * NODES, design, rms))
    return events


def loss(time, b, v, k, flux_ratio, ld):
    z = np.ascontiguousarray(np.hypot(b, v * time).ravel())
    return (1 - _quadratic_ld._quadratic_ld(z, k, *ld, 1)).reshape(time.shape) / (1 + flux_ratio)


def fit(events, radius, flux_ratio, ld):
    k = (radius / RS).decompose().value
    def model(p):
        result = []
        for sector, x, y, tt, design, rms in events:
            blocked = loss(tt, *p, k, flux_ratio, ld) @ WEIGHTS
            base = design @ np.linalg.lstsq(design, y + blocked, rcond=None)[0]
            result.append((sector, x, y - base, blocked, (y - base + blocked) / rms))
        return result
    def residual(p):
        return np.concatenate([s[-1] for s in model(p)])
    sol = least_squares(residual, [.92, 9.0], bounds=([0, .01], [1 + k, np.inf]), max_nfev=200)
    if not sol.success:
        raise RuntimeError(sol.message)
    b, v = sol.x
    return k, b, v, 2 * sol.cost, sol.nfev, model(sol.x)


def main():
    ev = datasets()
    rows = []
    profiles = [(f"{r:.2f} RJ", r*c.R_jup, c.M_jup, 0.) for r in [1.0, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.80, 2.00]]
    profiles += [("0.15 solar radii", .15*c.R_sun, .12*c.M_sun, .001)]
    curves = {}
    for ld in [(.35, .20), (.25, .25), (.45, .15)]:
        for name, radius, mass, flux in profiles:
            k, b, v, chi, nfev, model = fit(ev, radius, flux, ld)
            a = (c.G * (MS + mass) * (PERIOD / (2*np.pi))**2)**(1/3)
            g = v / (2*np.pi * a / (PERIOD * RS)).to_value(1/u.day)
            emin = abs(g**2 - 1)/(g**2 + 1)
            amp = (2*np.pi*c.G/PERIOD)**(1/3)*mass/(MS+mass)**(2/3)
            rows.append(dict(example=name, radius_Rj=(radius/c.R_jup).decompose().value, k=k, assumed_flux_ratio=flux, u1=ld[0], u2=ld[1], impact=b, speed_Rstar_day=v, chi2_white=chi, evaluations=nfev, emin_at_reference_mass=emin, circular_K_m_s=amp.to_value(u.m/u.s)))
            if ld == (.35,.20) and name in ("1.20 RJ","0.15 solar radii"):
                curves[name] = (model,k,b,v,flux)
    with (HERE/"eclipse_models.csv").open("w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    fig, ax = plt.subplots(figsize=(7.9,4.4),layout="constrained")
    model = curves["1.20 RJ"][0]
    for sector,x,y,blocked,res in model:
        show=abs(x)<.095
        ax.scatter(x[show]*24, y[show]*100, s=9,alpha=.35,label=f"TESS {sector}",edgecolor="none",zorder=1)
    t=np.linspace(-.095,.095,501)
    checks = {}
    for (name, (data,k,b,v,flux)), line, color, label in zip(curves.items(),["-","--"],["#262626","#c0364a"],["Giant planet, 1.20 Jupiter radii","Red dwarf, 0.15 solar radii"]):
        ax.plot(t*24,-100*loss(t,b,v,k,flux,(.35,.20)),line,color=color,lw=2.3,label=label)
        row = next(r for r in rows if r['example']==name and r['u1']==.35)
        mass = c.M_jup if flux==0 else .12*c.M_sun
        a = ((c.G*(MS+mass)*(PERIOD/(2*np.pi))**2)**(1/3)/RS).decompose().value
        p = batman.TransitParams()
        p.t0, p.per, p.rp, p.a = 0., PERIOD.value, k, a
        p.ecc, p.w, p.u, p.limb_dark = row["emin_at_reference_mass"], 90., [.35,.20], "quadratic"
        p.inc = np.rad2deg(np.arccos(b/(a*(1-p.ecc))))
        exact = (1-batman.TransitModel(p,t).light_curve(p))/(1+flux)
        checks[name] = dict(inclination_deg=p.inc, secondary_impact=b*(1+p.ecc)/(1-p.ecc),
                            sum_radii_in_Rstar=1+k, eccentricity=p.ecc,
                            K_m_s=row["circular_K_m_s"]*np.sin(np.deg2rad(p.inc))/np.sqrt(1-p.ecc**2),
                            peak_loss_ppt=1000*np.max(exact),
                            max_straight_path_error_ppm=1e6*max(abs(exact-loss(t,b,v,k,flux,(.35,.20)))))
    m1, m2 = (x[0] for x in curves.values())
    checks["max_native_cadence_profile_difference_ppt"] = max(np.max(abs(x[3]-y[3])) for x,y in zip(m1,m2))*1000
    checks["sample_count"] = sum(len(x[1]) for x in ev)
    (HERE/"orbit-examples.json").write_text(json.dumps(checks,indent=2)+"\n")
    ax.set(xlabel="Hours from each measured eclipse center",ylabel="Flux change (%)",xlim=(-2.25,2.25))
    ax.legend(ncol=2,fontsize=8,loc="lower left")
    ax.spines[['top','right']].set_visible(False)
    fig.savefig(HERE/"eclipse-models.png",dpi=190)
    for row in rows:
        if row['u1']==.35:
            print(row['example'],*(round(row[key],4) for key in ('impact','chi2_white','emin_at_reference_mass','circular_K_m_s')),row['evaluations'])
    print("sectors, counts and off-event scatter", [(s,len(x),round(rms*1000,2)) for s,x,_,_,_,rms in ev])


if __name__ == "__main__":
    main()
