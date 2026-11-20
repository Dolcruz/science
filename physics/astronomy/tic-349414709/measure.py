"""Measure the period, source localization and held-out ground-based eclipse depths."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from astropy.utils import iers
from scipy.optimize import least_squares


ROOT = Path(__file__).resolve().parent
SECTORS = (7, 34, 61, 88, 108)
TCE_PERIOD, TCE_EPOCH = 2.70894, 4293.7
HOST, NOMINAL, OTHER = ("TIC 349414709", "TIC 349414705", "TIC 349414726")
COLORS = {HOST: "#176c80", NOMINAL: "#a5541a", OTHER: "#61549b"}


def phase(t, period, epoch):
    return ((t - epoch) / period + 0.5) % 1 - 0.5


def primary_centers(t, y, sector):
    rows = []
    for n in range(round((min(t)-TCE_EPOCH)/TCE_PERIOD)-1,
                   round((max(t)-TCE_EPOCH)/TCE_PERIOD)+2):
        pred = TCE_EPOCH + n*TCE_PERIOD
        sel = abs(t-pred) < .34
        times, flux = t[sel], y[sel]
        if len(times) < 4:
            continue
        bins = np.arange(pred-.34, pred+.35, .02)
        med = [np.median(flux[m]) if (m := (times >= lo) & (times < lo+.02)).any()
               else np.inf for lo in bins]
        center = bins[np.argmin(med)] + .01
        dist = abs(times-center)
        if not ((times < center-.06).any() and (times > center+.06).any()):
            continue
        base = np.median(flux[dist > .09])
        if not (dist < .025).any() or base-np.median(flux[dist < .025]) < .003:
            continue
        near = dist < .09
        weights = np.maximum(0, base-flux[near]-.003)
        if weights.sum() > 0:
            rows.append((sector, n, np.average(times[near], weights=weights)))
    return rows


def pixel_center(img):
    yy, xx = np.indices(img.shape)
    mask = np.isfinite(img)
    x, y, v = xx[mask], yy[mask], img[mask]
    peak = np.argmax(v)
    def residual(par):
        amp, cx, cy, sx, sy, corr, background = par
        u, w = (x-cx)/sx, (y-cy)/sy
        return background + amp*np.exp(-.5*(u*u+w*w-2*corr*u*w)/(1-corr*corr))-v
    fit = least_squares(residual, [v[peak], x[peak], y[peak], 1, 1, 0, 0],
                        bounds=([0,-1,-1,.3,.3,-.7,-np.inf],
                                [np.inf,img.shape[1],img.shape[0],2,2,.7,np.inf]))
    return fit.x[1:3]


def event_depths(t, y, period, epoch, sector):
    rows = []
    for name, center in [('primary', 0), ('secondary', .505), ('control', .25)]:
        n = np.rint((t-epoch)/period-center).astype(int)
        for cycle in np.unique(n):
            q = n == cycle
            dx = (t[q]-epoch)/period-center-cycle
            inn = abs(dx) < .009
            left = (dx > -.070) & (dx < -.035)
            right = (dx > .035) & (dx < .070)
            if inn.sum() >= 2 and left.sum() >= 2 and right.sum() >= 2:
                base = (np.median(y[q][left])+np.median(y[q][right]))/2
                rows.append((sector, name, cycle, 100*(1-np.median(y[q][inn])/base)))
    return rows


def bochum_btjd(mjd_utc):
    # The matching observatory frames establish UTC for this field (see timing/README.md).
    site = EarthLocation.from_geodetic(-70.20128, -24.59867, 2817)
    direction = SkyCoord(114.51941708, -20.39278903, unit='deg')
    times = Time(mjd_utc, format='mjd', scale='utc', location=site)
    with iers.conf.set_temp('auto_download', False):
        barycentric = times.tdb + times.light_travel_time(direction, kind='barycentric')
    return barycentric.jd - 2457000


def ground_depths(ground):
    totals = []
    for (star, band), group in ground.groupby(['source', 'band']):
        distance = abs(group.phase)
        inside = distance < .018
        outside = (distance > .035) & (distance < .43)
        dip = np.median(group.mag[inside]) - np.median(group.mag[outside])
        totals.append((star, band, len(group), int(inside.sum()), int(outside.sum()),
                       dip, 100 * (1 - 10 ** (-.4 * dip))))
    return pd.DataFrame(totals, columns=['source', 'band', 'all_epochs', 'in_eclipse',
                                         'out_of_eclipse', 'dip_mag', 'flux_loss_pct'])


def main():
    tess = np.load(ROOT/'tess-curves.npz')
    curves = {s:(tess[f'time{s}'],tess[f'flux{s}']) for s in SECTORS}
    rows = [r for s,(t,y) in curves.items() for r in primary_centers(t,y,s)]
    ev = pd.DataFrame(rows, columns=['sector','cycle','btjd'])
    for _ in range(3):
        period, epoch = np.polyfit(ev.cycle, ev.btjd, 1)
        ev = ev[abs(ev.btjd-epoch-period*ev.cycle) < .06].copy()
    ev['residual_min'] = (ev.btjd-epoch-period*ev.cycle)*1440
    ev.to_csv(ROOT/'eclipse-times.csv',index=False)
    loo = [np.polyfit(ev[ev.sector!=s].cycle,ev[ev.sector!=s].btjd,1)[0] for s in SECTORS]
    phases = [r for s,(t,y) in curves.items() for r in event_depths(t,y,period,epoch,s)]
    phot = pd.DataFrame(phases,columns=['sector','feature','cycle','depth_pct'])
    phot.to_csv(ROOT/'tess-event-depths.csv',index=False)

    ground = pd.read_csv(ROOT/'bochum-curves.csv')
    mjd = ground.mjd_utc.to_numpy()
    ground['phase'] = phase(bochum_btjd(mjd), period, epoch)
    summary = ground_depths(ground)
    summary.to_csv(ROOT/'ground-depths.csv', index=False)

    # Compare possible offsets of the effective mid-exposure time in a combined frame.
    sensitivity = [summary.assign(time_basis='observatory UTC', offset_s=0)]
    for seconds in (5, 45, 90, 120):
        btjd = bochum_btjd(mjd + seconds / 86400)
        depths = ground_depths(ground.assign(phase=phase(btjd, period, epoch)))
        sensitivity.append(depths.assign(time_basis='observatory UTC', offset_s=seconds))
    metadata_btjd = Time(mjd, format='mjd', scale='tcb').tdb.jd - 2457000
    depths = ground_depths(ground.assign(phase=phase(metadata_btjd, period, epoch)))
    sensitivity.append(depths.assign(time_basis='VOTable TCB', offset_s=0))
    pd.concat(sensitivity, ignore_index=True).to_csv(ROOT/'timing'/'sensitivity.csv', index=False)
    pix = np.load(ROOT/'difference-images.npz')
    mean_img = np.mean(pix['events'],axis=0)
    from scipy.ndimage import map_coordinates
    images = [mean_img,*pix['events']]
    cent=[]
    for i,im in enumerate(images):
        x,y = pixel_center(im)
        rd=[map_coordinates(pix[k],[[y],[x]],order=1)[0] for k in ('ra_deg','dec_deg')]
        cent.append((i,x,y,*rd))
    centers=pd.DataFrame(cent,columns=['stack_0_or_eclipse','x_pixel','y_pixel','ra_deg','dec_deg'])
    centers.to_csv(ROOT/'pixel-centers.csv',index=False)
    print(f'{len(ev)} primary centers; epoch BTJD {epoch:.7f}, period {period:.9f} d')
    print(f'Leave-one-sector-out periods {min(loo):.9f} to {max(loo):.9f} d')
    print(summary.round(4).to_string(index=False))
    phot['parity']=phot.cycle%2
    print(phot.groupby(['sector','feature','parity']).depth_pct.median().round(3).unstack())
    print(centers.round(6).to_string(index=False))
    figure(curves,period,epoch,ground,mean_img,pix,centers)


def figure(curves,period,epoch,ground,img,pix,centers):
    fig,axes=plt.subplots(2,2,figsize=(10,7.4),layout='constrained')
    def curve(ax,s,left,right):
        t,y=curves[s]
        ph=phase(t,period,epoch)
        if left>0:
            ph=ph%1
        edges=np.linspace(left,right,54)
        med=[np.median(y[m]) if (m := (ph>=a)&(ph<b)).any() else np.nan
             for a,b in zip(edges[:-1],edges[1:])]
        color=COLORS[NOMINAL] if s==108 else COLORS[HOST]
        ax.plot(.5*(edges[:-1]+edges[1:]),med,color=color,alpha=.9 if s==108 else .48,
                lw=1.5 if s==108 else 1.2)
    for col,(lo,hi,name) in enumerate([(-.095,.095,'Primary eclipse'),(.42,.59,'Secondary eclipse')]):
        ax=axes[0,col]
        for sec in SECTORS: curve(ax,sec,lo,hi)
        ax.set_title(name,loc='left',fontweight='bold');ax.set_xlabel('Orbital phase');ax.set_ylabel('Relative TESS flux')
    axes[0,0].legend(handles=[Line2D([],[],color=COLORS[HOST],label='TIC 349414709 · sectors 7, 34, 61, 88'),
                              Line2D([],[],color=COLORS[NOMINAL],label='TIC 349414705 · sector 108')],fontsize=8)
    ax=axes[1,0]
    for i,star in enumerate([HOST,NOMINAL,OTHER]):
        g=ground[ground.source==star].copy()
        base=g[abs(g.phase)>.05].groupby('band').mag.median()
        norm=g.mag-g.band.map(base)
        q=abs(g.phase)<.12
        ax.scatter(g.phase[q],norm[q]+.19*i,s=12,alpha=.65,color=COLORS[star],label=star)
        ax.axhline(.19*i,lw=.6,c=COLORS[star],alpha=.45)
    ax.invert_yaxis();ax.set_xlabel('Phase predicted from TESS alone');ax.set_ylabel('Differential magnitude + offset')
    ax.set_title('Ground photometry at three stars',loc='left',fontweight='bold')
    ax.legend(fontsize=8)
    ax=axes[1,1];hostra,hostdec=114.51941708,-20.39278903
    east=(pix['ra_deg']-hostra)*np.cos(np.deg2rad(hostdec))*3600
    north=(pix['dec_deg']-hostdec)*3600
    ax.pcolormesh(east,north,img,shading='nearest',cmap='Greys',rasterized=True)
    x=(centers.ra_deg-hostra)*np.cos(np.deg2rad(hostdec))*3600
    y=(centers.dec_deg-hostdec)*3600
    ax.scatter(x[1:],y[1:],s=12,color='#d7ad2a',label='Individual primary eclipses')
    stars=pd.read_csv(ROOT/'tic-stars.csv')
    for star in [HOST,NOMINAL,OTHER]:
        r=stars[stars.ID==int(star.split()[-1])].iloc[0]
        elapsed = Time(2457000 + epoch, format='jd', scale='tdb').jyear - 2000
        east_offset = (r.ra-hostra)*np.cos(np.deg2rad(hostdec))*3600 + r.pmRA*elapsed/1000
        north_offset = (r.dec-hostdec)*3600 + r.pmDEC*elapsed/1000
        ax.scatter(east_offset,north_offset,
                   marker='+',s=95,lw=1.8,c=COLORS[star],label=star)
    ax.set_aspect('equal');ax.set_xlim(43,-43);ax.set_ylim(-34,34)
    ax.set_xlabel('East offset (arcsec)');ax.set_ylabel('North offset (arcsec)')
    ax.set_title('TESS eclipse difference image',loc='left',fontweight='bold')
    ax.legend(fontsize=7,loc='upper right',framealpha=.88)
    fig.savefig(ROOT/'eclipse-source.png',dpi=180)
    plt.close(fig)


if __name__=='__main__':
    main()
