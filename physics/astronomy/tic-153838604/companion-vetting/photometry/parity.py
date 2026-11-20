"""Compare the four eclipses after exposure integration, with same-sector noise injections."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits

OUT = Path(__file__).resolve().parent
DISCOVERY = OUT.parents[1] / "duotransit"
sys.path.insert(0, str(DISCOVERY))
from measure import fit_event, triangular_profile

PRIMARY = np.genfromtxt(DISCOVERY / "measurements.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
SECTORS = [4,5,31,32,97,98]
EPOCH, PERIOD = 1447.10503234, 56.07935938


def read(sector):
    name = f"hlsp_qlp_tess_ffi_s{sector:04d}-0000000153838604_tess_v01_llc.fits"
    path = (OUT if sector in (4,31) else DISCOVERY) / "fits" / name
    with fits.open(path) as h:
        d=h[1].data
        base="DET_FLUX" if "DET_FLUX" in d.names else "KSPSAP_FLUX"
        keys={"default":base,"small":base+"_SML","large":base+"_LAG","raw":"SAP_FLUX"}
        good=(d["QUALITY"]==0)&np.isfinite(d["TIME"])&np.isfinite(d[base])
        curves={name: np.array(d[key][good],float) for name,key in keys.items()}
        return np.array(d["TIME"][good]),np.array(d["CADENCENO"][good]),curves,h[1].header["TIMEDEL"],hashlib.sha256(path.read_bytes()).hexdigest()


def write_rows(name,rows):
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def sum_draws(coeff, controls):
    result=np.array([0.0])
    for weight, errors in zip(coeff,controls):
        result = (result[:,None]+weight*errors).ravel()
    return result


def main():
    metrics=[]; windows=[]; errors={}; sector_info=[]
    for s in SECTORS:
        t,cad,f,exp,digest=read(s)
        sector_info.append(dict(sector=s,quality_zero_cadences=len(t),cadence_sec=round(exp*86400),start_btjd=t[0],end_btjd=t[-1],sha256=digest))
        if s not in PRIMARY["sector"]:continue
        rec=PRIMARY[PRIMARY["sector"]==s][0]; mid=rec["fitted_btjd"]; y=f["default"]
        for aperture,v in f.items():
            finite=np.isfinite(v)
            centre,depth,dur,*_=fit_event(t[finite],v[finite],mid,exp)
            metrics.append(dict(sector=s,cycle=int(rec["cycle"]),aperture=aperture,centre_btjd=centre,depth_ppt=depth*1000,duration_hours=dur))
        # Transfer the original sampling mask around the eclipse to each clean patch.
        used=np.abs(t-mid)<.30
        relative_time=t[used]-mid
        delta_cad=cad[used]-cad[np.argmin(abs(t-mid))]
        inner=np.abs(relative_time)<.12
        sector_errors={name:[] for name in f}
        for control in np.arange(t[0]+.31,t[-1]-.31,.62):
            if abs(control-mid)<.62:continue
            k=cad[np.argmin(abs(t-control))]+delta_cad
            ix=np.searchsorted(cad,k); ix=np.clip(ix,0,len(cad)-1)
            valid=(cad[ix]==k)&(abs(t[ix]-control)<.33)
            if not np.all(valid[inner]) or valid.sum()<.85*len(k):continue
            x=relative_time[valid]
            for aperture,series in f.items():
                background=series[ix[valid]]
                if not np.isfinite(background).all():continue
                # All sectors receive the same underlying 15 ppt, 2.5-hour triangle.
                injected=background - np.median(background)*.015*triangular_profile(x,2.5/48,exp)
                m,d,w,*_=fit_event(x,injected,0.,exp)
                sector_errors[aperture].append([m,d*1000-15,w-2.5])
                windows.append(dict(sector=s,aperture=aperture,control_btjd=control,timing_error_min=m*1440,
                                    depth_error_ppt=d*1000-15,width_error_hours=w-2.5))
        for ap,records in sector_errors.items():
            errors.setdefault(ap,[]).append(np.asarray(records))
    write_rows("sectors.csv",sector_info);write_rows("apertures.csv",metrics);write_rows("parity_injections.csv",windows)
    nominal=[r for r in metrics if r["aperture"]=="default"]
    cycles=np.array([r["cycle"] for r in nominal])
    parity=cycles%2
    coef=np.where(parity==0,.5,-.5)
    # At fixed period the odd-vs-even time bias is degenerate with timing errors.
    # Fit a slope, intercept, and odd-event timing displacement simultaneously.
    X=np.column_stack((np.ones(4),cycles,parity))
    G=np.linalg.inv(X.T@X)@X.T
    summary={}
    for name,col,weights,scale in [('depth_even_minus_odd_ppt',1,coef,1.0),('duration_even_minus_odd_h',2,coef,1.0),('odd_time_offset_min',0,G[2],1440.)]:
        key=['centre_btjd','depth_ppt','duration_hours'][col]
        values=np.array([r[key] for r in nominal])
        estimate=float(weights@values)*scale
        draws=sum_draws(weights,[e[:,col] for e in errors["default"]])*scale
        low,high=estimate-np.quantile(draws,[.975,.025])
        summary[name]=dict(estimate=estimate,interval_95=[low,high],control_combinations=len(draws))
    for aperture in ['small','large','raw']:
        vals=[r['depth_ppt'] for r in metrics if r['aperture']==aperture]
        estimate=float(coef@vals)
        draws=sum_draws(coef,[e[:,1] for e in errors[aperture]])
        summary[aperture+'_depth_even_minus_odd_ppt']=dict(estimate=estimate,
                   interval_95=list(estimate-np.quantile(draws,[.975,.025])))
    summary['empirical_counts']=[len(x) for x in errors['default']]
    summary['idealized_tic_contamination_multiplier']=1.016354
    (OUT/'parity.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(summary)


if __name__=="__main__":
    main()
