"""Compare calibrated-time vertical and horizontal recordings for two Brawley events."""
import argparse
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from survey import HERE, STATIONS, FILTER, TEMPLATE_MAGNITUDE, write_table


def section(wave, a, b):
    return wave[round((a+30)*100):round((b+30)*100)]


def correlation(a, b):
    return float(np.corrcoef(a,b)[0,1])


def measure(chips, output):
    output.mkdir(exist_ok=True, parents=True)
    with np.load(chips) as z:
        wave = {name: signal.sosfiltfilt(FILTER,z[name]) for name in z.files}
    with (HERE/'reference-picks.csv').open() as f:
        phases = list(csv.DictReader(f))
    rows, picks = [], []
    fig, axes = plt.subplots(len(STATIONS),2,figsize=(10,7.6),sharex=True)
    for i,sta in enumerate(STATIONS):
        for j,channel in enumerate(('HHZ','HHN')):
            x,y = [wave[f'{which}_{sta}_{channel}'] for which in ('reference','candidate')]
            t,c = section(x,1,13), section(y,1,13)
            rms_ratio = np.sqrt(np.mean(c*c)/np.mean(t*t))
            peak_ratio = np.ptp(c)/np.ptp(t)
            noise = section(y,-16,-4)
            scale = np.dot(t,c)/np.dot(t,t)
            rows.append(dict(station=sta,channel=channel,
                             cc=correlation(t,c),peak_to_peak_ratio=peak_ratio,
                             rms_ratio=rms_ratio,regression_ratio=scale,
                             rms_to_prearrival=np.sqrt(np.mean(c*c)/np.mean(noise*noise)),
                             peak_relative_magnitude=TEMPLATE_MAGNITUDE+np.log10(peak_ratio)))
            ax = axes[i,j]
            seconds = np.arange(-1,14,.01)
            norm = np.max(np.abs(c))
            ax.plot(seconds,section(x,-1,14)*scale/norm, color='#db7945',lw=1.15,
                    alpha=.85,label='Reference, scaled')
            ax.plot(seconds,section(y,-1,14)/norm, color='#214b68',lw=.7,label='Candidate')
            ax.set_yticks([])
            ax.spines[['top','right','left']].set_visible(False)
            ax.text(.01,.85,f'{sta}  ·  r = {correlation(t,c):.2f}',
                    transform=ax.transAxes,fontsize=9)
            if i == 0: ax.set_title('Vertical' if channel == 'HHZ' else 'North–south')
            if i == len(STATIONS)-1: ax.set_xlabel('Seconds from respective origin')
        for row in (r for r in phases if r['station']==sta):
            phase = row['phase']
            channel = 'HHZ' if phase=='P' else 'HHN'
            x,y = [wave[f'{which}_{sta}_{channel}'] for which in ('reference','candidate')]
            p=(datetime.fromisoformat(row['utc'])-datetime.fromisoformat(row['origin'])).total_seconds()
            ref=section(x,p-.25,p+1.15)
            lags=np.arange(-25,26)/100
            scores=np.array([correlation(ref,section(y,p-.25+d,p+1.15+d)) for d in lags])
            idx=int(np.argmax(scores))
            picks.append(dict(station=sta,phase=phase,reference_pick_channel=row['channel'],
                              measured_channel=channel,reference_arrival_s=p,
                              peak_shift_s=lags[idx],peak_cc=scores[idx],zero_lag_cc=scores[25]))
            axes[i,0 if phase=='P' else 1].axvline(p,color='#888',ls=':',lw=.8)
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
    fig.subplots_adjust(left=.04,right=.99,top=.95,bottom=.10,hspace=.4,wspace=.06)
    fig.savefig(output/'waveforms.png',dpi=160)
    plt.close(fig)
    write_table(output/'station-measurements.csv',rows)
    write_table(output/'phase-comparisons.csv',picks)
    for row in rows:
        print(row['station'],row['channel'],f"r={row['cc']:.3f}, amplitude={row['peak_to_peak_ratio']:.3f}, SNR={row['rms_to_prearrival']:.1f}")
    for r in picks:
        print(r['station'],r['phase'],f"{r['peak_shift_s']:+.2f}",f"{r['peak_cc']:.3f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chips', type=Path, default=HERE/'native-cutouts.npz')
    parser.add_argument('--output', type=Path, default=Path('results'))
    args=parser.parse_args()
    measure(args.chips,args.output)
