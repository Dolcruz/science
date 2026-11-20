"""Compare matched low-Sun terrain at 78–82 degrees incidence before and after formation."""
from survey import setup, scan
import cv2
import json,sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
setup()
BEFORES=['M178510938LC','M1109154536RC']
AFTER='M1185701417RC'
def run(root,out):
    points=dict(np.load(root/'terrain/cross-sun-centers.npz'))
    ids=BEFORES+[AFTER];imgs=[]
    for k in ids:
        a=np.load(root/'tiles'/(k+'.npy'))
        imgs.append(np.log(np.maximum(100.,cv2.getRectSubPix(a,(193,193),tuple(points[k].astype('f4'))))).astype(float))
    y,x=np.indices(imgs[0].shape);r=np.hypot(y-96,x-96);mask=(r>=12)&(r<=90)
    # A shared smoothing kernel makes image samples comparable. Fit translation,
    # intensity gain and offset on the surrounding terrain. The event is masked.
    phot=[];outputs={}
    for source,im in zip(BEFORES,imgs):
        for sig in [1.,2.]:
            a=gaussian_filter(im,sig);b=gaussian_filter(imgs[-1],sig)
            def warp(z):
                return map_coordinates(a,[y+z[1],x+z[0]],order=1,mode='nearest')*z[2]+z[3]
            def residual(z):return (warp(z)-b)[mask]
            fit=least_squares(residual,[0,0,1,0],loss='soft_l1',f_scale=.03,bounds=([-5,-5,.1,-10],[5,5,2,10]),diff_step=[.01,.01,.00001,.00001])
            d=b-warp(fit.x);d-=gaussian_filter(d,12)
            outputs[source+str(sig)]=d
            centers=[(i,j) for i in range(-72,73,12) for j in range(-72,73,12) if np.hypot(i,j)>12]
            def stat(i,j):
                rr=np.hypot(x-96-i,y-96-j);m=rr<=3
                return d[m].mean()-d[(rr>=6)&(rr<12)].mean(),d[m].max()-d[m].min()
            core,span=stat(0,0);c,h=np.array([stat(i,j) for i,j in centers]).T
            phot.append(dict(before=source,after=AFTER,extra_blur_sigma_px=sig,dx=fit.x[0],dy=fit.x[1],gain=fit.x[2],log_aperture_excess=core,control_min=c.min(),control_max=c.max(),control_percentile=100*(c<core).mean(),central_peak_to_trough=span,peak_to_trough_control_percentile=100*(h<span).mean(),n_controls=len(c)))
    pd.DataFrame(phot).to_csv(out/'grazing-comparison.csv',index=False)
    np.savez_compressed(out/'grazing-residuals.npz',**outputs)
    fig,ax=plt.subplots(2,4,figsize=(10,5.7),layout='constrained')
    lab=['2011-12-14','2012-12-03','2015-05-08','2015 minus 2011']
    for i,h in enumerate([38,10]):
        for j,a in enumerate(imgs+[outputs[BEFORES[0]+'1.0']]):
            c=ax[i,j];chip=a[96-h:97+h,96-h:97+h]
            if j<3:vmin,vmax=np.percentile(chip,[2,98]);c.imshow(chip,cmap='gray',vmin=vmin,vmax=vmax,interpolation='nearest')
            else:c.imshow(chip,cmap='RdBu_r',vmin=-.07,vmax=.07,interpolation='nearest')
            if i==0:c.set_title(lab[j]);c.plot([h,h],[h-14,h-7],color='#00a6bb',lw=1);c.plot([h+7,h+14],[h,h],color='#00a6bb',lw=1)
            c.axis('off')
    fig.savefig(out/'grazing-comparison.png',dpi=145);plt.close(fig)
    print(pd.DataFrame(phot).round(5).to_string(index=False))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
