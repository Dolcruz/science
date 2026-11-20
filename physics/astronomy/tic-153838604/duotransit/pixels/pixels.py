"""Localize the flux lost in each of two TESS transits. Supply a directory for the downloaded cutouts."""
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import numpy as np
import requests
from scipy.optimize import least_squares

OUT=Path(__file__).resolve().parent
RA,DEC=68.07396,-47.6088
Y,X=np.mgrid[0:9,0:9]


def difference(t,cube,tc):
    dt=t-tc
    before=(dt>=-.20)&(dt<=-.09)
    after=(dt>=.09)&(dt<=.20)
    inside=abs(dt)<=.04
    if min(before.sum(), after.sum(), inside.sum())<20:
        return None
    # Interpolate in time between the two local off-transit images.
    a,b=t[before].mean(),t[after].mean()
    weight=(t[inside].mean()-a)/(b-a)
    loss=(1-weight)*cube[before].mean(0)+weight*cube[after].mean(0)-cube[inside].mean(0)
    border=(X==0)|(X==8)|(Y==0)|(Y==8)
    A=np.stack([np.ones_like(X),X-4,Y-4],axis=-1)
    sky=np.linalg.lstsq(A[border],loss[border],rcond=None)[0]
    return loss-A@sky


def centroid(im):
    # The initial center is the brightest loss pixel anywhere in the stamp.
    iy,ix=np.unravel_index(im.argmax(),im.shape)
    def residual(v):
        a,x,y,sx,sy,r,offset=v
        dx,dy=(X-x)/sx,(Y-y)/sy
        return (offset+a*np.exp(-.5*(dx**2+dy**2-2*r*dx*dy)/(1-r*r))-im).ravel()
    fit=least_squares(residual,[im.max(),ix,iy,1,1,0,0],
                      bounds=([0,-.5,-.5,.35,.35,-.85,-np.inf],
                              [np.inf,8.5,8.5,3,3,.85,np.inf]))
    if not fit.success:
        raise RuntimeError(fit.message)
    return fit.x[1:3]


def evaluate(sector,tc,cache=OUT/'cache'):
    cache.mkdir(exist_ok=True,parents=True)
    base='https://mast.stsci.edu/tesscut/api/v0.1/astrocut'
    prep=requests.Request('GET',base,params=dict(ra=RA,dec=DEC,x=9,y=9,units='px',sector=sector)).prepare()
    path=cache/f's{sector}.zip'
    if not path.exists():
        r=requests.get(prep.url)
        r.raise_for_status()
        path.write_bytes(r.content)
    with zipfile.ZipFile(path) as z:
        raw=z.read(next(n for n in z.namelist() if n.endswith('.fits')))
    with fits.open(io.BytesIO(raw)) as h:
        d=h[1].data
        ok=(d['QUALITY']==0)&np.isfinite(d['TIME'])&np.isfinite(d['FLUX']).all(axis=(1,2))
        t=np.asarray(d['TIME'][ok],float)
        cube=np.asarray(d['FLUX'][ok],float)
        wcs=WCS(h[2].header)
        xy=np.array(wcs.world_to_pixel_values(RA,DEC))
        det=[h[0].header['CAMERA'],h[0].header['CCD']]
    im=difference(t,cube,tc)
    found=centroid(im)
    # Independent windows elsewhere in the same sector measure the local systematic floor.
    null=np.array([v for c in np.arange(t.min()+.21,t.max()-.20,.45)
                   if abs(c-tc)>.43 and (v:=difference(t,cube,c)) is not None])
    near=np.hypot(X-xy[0],Y-xy[1])<1.8
    nullsum=null[:,near].sum(1)
    source=im[near].sum()
    # Inject the measured loss image in every control window; include pointing and shape variability.
    shifts=np.array([centroid(test+im)-found for test in null])
    summary=dict(sector=sector,center_BTJD=tc,camera=det[0],ccd=det[1],expected_xy=xy.tolist(),
                 loss_xy=found.tolist(),radial_offset_pixels=float(np.linalg.norm(found-xy)),
                 control_windows=len(null),scatter_xy_pixels=np.std(shifts,axis=0,ddof=1).tolist(),
                 positive_control_max_electrons_per_second=float(nullsum.max()),
                 observed_aperture_loss_electrons_per_second=float(source),
                 empirical_scatter_electrons_per_second=float(nullsum.std(ddof=1)),
                 url=prep.url,extracted_fits_SHA256=hashlib.sha256(raw).hexdigest())
    np.savez_compressed(OUT/f'difference_s{sector}.npz',loss=im,control_images=null)
    return im,summary


if __name__=='__main__':
    cache=Path(sys.argv[1]) if len(sys.argv)>1 else OUT/'cache'
    results=[evaluate(97,3970.674030,cache),evaluate(98,4026.757359,cache)]
    stats=[r for _,r in results]
    (OUT/'localization.json').write_text(json.dumps(stats,indent=2))
    fig,ax=plt.subplots(1,2,figsize=(8,3.7),layout='constrained')
    for a,(im,s) in zip(ax,results):
        handle=a.imshow(im,origin='lower',cmap='viridis',vmin=-.65,vmax=3.1)
        a.scatter(*s['expected_xy'],s=130,facecolors='none',edgecolors='white',lw=1.5,label='Catalog position')
        a.scatter(*s['loss_xy'],marker='+',s=120,color='#f47855',lw=1.7,label='Center of dimming')
        a.set(title=f"TESS sector {s['sector']}  Â·  CCD {s['ccd']}",xlabel='Detector column (pixels)',ylabel='Detector row (pixels)')
    ax[0].legend(fontsize=8,loc='lower left',framealpha=.85)
    fig.colorbar(handle,ax=ax,label='Flux lost (electrons per second per pixel)',shrink=.83)
    fig.savefig(OUT/'difference-images.png',dpi=180)
    print(json.dumps(stats,indent=2))
