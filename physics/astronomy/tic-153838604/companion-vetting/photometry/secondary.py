"""Measure the visibility of a second eclipse as a function of phase and duration."""
import gzip
import csv
import json

import numpy as np
from matplotlib import pyplot as plt

from parity import EPOCH, OUT, PERIOD, PRIMARY, SECTORS, read, sum_draws, triangular_profile, write_rows


def matched(time, flux, exposure, centre, duration):
    # Flux in ppt is relative to the median local continuum. Positive depth is a dip.
    window=max(.30,2*duration)
    a,b=np.searchsorted(time,[centre-window,centre+window])
    x=time[a:b]-centre
    y=flux[a:b]
    inner=np.abs(x)<duration/2
    before=x < -duration/2
    after=x > duration/2
    if (inner.sum()<max(2,.70*duration/exposure) or
        min(before.sum(),after.sum())<.60*(window-duration/2)/exposure):
        return np.nan
    y=(y/np.median(y[~inner])-1)*1000
    h=triangular_profile(x,duration/2,exposure)
    # Project the depth template orthogonally to a constant and a local linear trend.
    dx=x-x.mean()
    h0=h-h.mean()-dx*(dx@h)/(dx@dx)
    return -(h0@y)/(h0@h0)


def quantile_lower(values,alpha):
    # Lower order statistic for a one-sided, finite-sample rank prediction.
    # Its validity requires exchangeability between the control and test windows.
    k=int(np.floor(alpha*(len(values)+1)))
    return float(np.sort(values)[k-1]) if k>0 else None


def main():
    phases=[]; controls=[]; mids=[]; reports={}; joint=[]; shifted=[]
    fig,axes=plt.subplots(2,1,figsize=(9.2,5.1),sharex=True,layout="constrained")
    ngrid=2*int(np.ceil(PERIOD/(10/1440)/2))
    step=PERIOD/ngrid
    actual=np.array(PRIMARY['fitted_btjd'])
    highres=2*ngrid
    for hours in [1.25,2.5,5.0]:
        duration=hours/24
        trials={};cal={}; control_samples={}; half_curves={}
        for sector in SECTORS:
            time,_,curves,exp,_=read(sector)
            flux=curves['default']
            window=max(.30,2*duration)
            samples=[]
            for centre in np.arange(time[0]+window,time[-1]-window,2*window):
                if min(abs(actual-centre))<2*window:continue
                value=matched(time,flux,exp,centre,duration)
                if np.isfinite(value):samples.append(value)
            control_samples[sector]=np.asarray(samples)
            lower=quantile_lower(samples,.05)
            sigma=float(np.std(samples,ddof=1)) if len(samples)>1 else np.nan
            controls.append(dict(sector=sector,duration_h=hours,windows=len(samples),mean_ppt=np.mean(samples),
                    scatter_ppt=sigma,lower_05_rank_ppt=lower))
            cal[sector]=(lower,sigma)
            for j in range(int(np.ceil((time[0]+window-EPOCH)/step)),int(np.floor((time[-1]-window-EPOCH)/step))+1):
                centre=EPOCH+j*step
                if min(abs(centre-actual))<2*window:continue
                value=matched(time,flux,exp,centre,duration)
                if np.isfinite(value):trials.setdefault(j%highres,[]).append((sector,centre,value))
            for n in range(int(np.ceil((time[0]-EPOCH)/PERIOD-.5)),int(np.floor((time[-1]-EPOCH)/PERIOD-.5))+1):
                centre=EPOCH+(n+.5)*PERIOD
                value=matched(time,flux,exp,centre,duration)
                raw=matched(time,curves['raw'],exp,centre,duration)
                if np.isfinite(value):
                    half_curves[(sector,centre)]=(time,flux,exp)
                    mids.append(dict(duration_h=hours,sector=sector,btjd=centre,det_depth_ppt=value,raw_depth_ppt=raw,control_scatter_ppt=sigma,
                                     one_sided_upper_ppt=max(0,value-lower) if lower is not None else None))
        observed=[r for r in mids if r['duration_h']==hours]
        weights=np.array([1/r['control_scatter_ppt']**2 for r in observed])
        weights=weights/weights.sum()
        combination=sum_draws(weights,[control_samples[r['sector']] for r in observed])
        value=float(weights@np.array([r['det_depth_ppt'] for r in observed]))
        raw_value=float(weights@np.array([r['raw_depth_ppt'] for r in observed]))
        joint.append(dict(duration_h=hours,qualifying_sectors=" ".join(str(r["sector"]) for r in observed),
                          weighted_depth_ppt=value,weighted_raw_depth_ppt=raw_value,
                          empirical_control_combinations=len(combination),
                          nominal_upper_95_ppt=max(0.,value-np.quantile(combination,.05)),
                          empirical_scatter_ppt=np.std(combination)))
        for minutes in range(-30,31):
            test=[matched(*half_curves[r['sector'],r['btjd']],r['btjd']+minutes/1440,duration)
                  for r in observed]
            amplitude=float(weights@np.array(test))
            shifted.append(dict(duration_h=hours,offset_min=minutes,weighted_depth_ppt=amplitude,
                                nominal_upper_95_ppt=max(0.,amplitude-np.quantile(combination,.05))
                                if np.isfinite(amplitude) else np.nan))
        for multiplier in [1,2]:
            bins=multiplier*ngrid
            out=[]
            for j in range(bins):
                phase=j/bins
                # Remove the full neighbourhood of each known eclipse at this orbital period.
                dist_primary=abs(j/ngrid-round(j/ngrid))*PERIOD
                if dist_primary<2*max(.30,2*duration):continue
                obs=list(trials.get(j,[]))
                if multiplier==1:obs+=trials.get(j+ngrid,[])
                qualified=[o for o in obs if cal[o[0]][0] is not None]
                if qualified:
                    # The witnessing sector is chosen with its control noise, independently
                    # of the in-window fitted depth. Ties use the earlier physical epoch.
                    sector,centre,depth=min(qualified,key=lambda o:(cal[o[0]][1],o[1]))
                    upper=max(0,depth-cal[sector][0])
                else:
                    sector=centre=depth=upper=None
                row=dict(orbit_multiple=multiplier,duration_h=hours,phase=phase,covered_epochs=len(obs),
                         calibrated_epochs=len(qualified),witness_sector=sector,witness_btjd=centre,
                         depth_ppt=depth,conditional_upper_ppt=upper)
                phases.append(row);out.append(row)
            U=np.array([np.nan if r['conditional_upper_ppt'] is None else r['conditional_upper_ppt'] for r in out])
            summary=dict(searchable_grid_points=len(out),total_grid_points=bins,covered_points=sum(r['covered_epochs']>0 for r in out),
                         repeated_coverage_points=sum(r['covered_epochs']>1 for r in out),
                         calibrated_coverage_points=int(np.isfinite(U).sum()),
                         fraction_upper_below={str(d):float(np.mean(U<d)) for d in [2,3,5,10,15]},
                         quantile_upper_ppt=list(np.nanquantile(U,[.5,.9,.95,1.])))
            reports[f'{multiplier}P_{hours}h']=summary
            if hours==2.5:
                ax=axes[multiplier-1];p=np.array([r['phase'] for r in out])
                ax.scatter(p,U,s=1.0,color="#286488",rasterized=True)
                ax.set(ylabel="Upper depth (ppt)",title=f"{multiplier*PERIOD:.3f}-day orbit  |  2.5-hour eclipse")
                ax.set_xlim(0,1);ax.set_ylim(bottom=0);ax.grid(alpha=.18)
    axes[-1].set_xlabel("Orbital phase relative to the first observed eclipse")
    fig.savefig(OUT/"phase-sensitivity.png",dpi=165)
    write_rows('noise_controls.csv',controls);write_rows('opposite_phase.csv',mids)
    write_rows('opposite_phase_joint.csv',joint);write_rows('opposite_phase_offset.csv',shifted)
    with gzip.open(OUT/'phase_sensitivity.csv.gz','wt',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=phases[0]);w.writeheader();w.writerows(phases)
    (OUT/'phase_summary.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps(reports,indent=2))


if __name__=="__main__":
    main()
