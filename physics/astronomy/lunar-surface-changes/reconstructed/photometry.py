"""Measure fixed-aperture contrast, response width and radial residuals at the new marking."""
from survey import setup,scan,A,B
from pathlib import Path
import json,sys
import cv2
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
setup()
ORDER=[B,"M1117402542LC",A,"M1193942227LC","M1209240188LC","M1446530029RC"]
DATES=["2012-03-19","2013-03-08","2014-02-26","2015-08-11","2016-02-04","2023-08-13"]

def calc(raw,out):
    out.mkdir(exist_ok=True, parents=True)
    cube=np.load(raw)
    imgs=[cube[k].astype(float) for k in ORDER]
    yy,xx=np.indices(imgs[0].shape)
    mid=xx.shape[0]//2
    x=xx-mid;y=yy-mid
    r=np.hypot(x,y)
    def phot(im,rr):
        return np.log(np.mean(im[rr<=2.5])/np.mean(im[(rr>6)&(rr<12)]))
    # Centers spaced 24 pixels so annuli do not overlap.
    centers=[(i,j) for i in range(-72,73,24) for j in range(-72,73,24) if (i,j)!=(0,0)]
    c=np.array([[phot(im,np.hypot(x-i,y-j)) for i,j in centers] for im in imgs])
    target=np.array([phot(im,r) for im in imgs])
    dc=c-c[:2].mean(axis=0)
    dt=target-target[:2].mean()
    rows=[]
    for k,n in enumerate(ORDER):
        rows.append(dict(product=n,date=DATES[k],core_log_contrast=target[k],contrast_relative_to_pre=dt[k],local_control_count=len(centers),control_median=np.median(dc[k]),control_min=dc[k].min(),control_max=dc[k].max(),control_p025=np.quantile(dc[k],.025),control_p975=np.quantile(dc[k],.975)))
    pd.DataFrame(rows).to_csv(out/'chronology.csv',index=False)
    ratios=[np.log(im)-(.5*np.log(imgs[0])+.5*np.log(imgs[1])) for im in imgs[2:]]
    m=np.median(ratios,axis=0)
    def fit(a):
        good=r<11;data=a[good];xg=x[good];yg=y[good]
        def err(p):
            dx=xg-p[0];dy=yg-p[1];ca=np.cos(p[4]);sa=np.sin(p[4])
            large=(dx*ca+dy*sa)/p[2];small=(-dx*sa+dy*ca)/p[3]
            return data-(p[5]*np.exp(-.5*(large**2+small**2))+p[6]+p[7]*xg+p[8]*yg)
        p=least_squares(err,[0,0,2,1.2,.1,.17,np.median(data),0,0],bounds=([-4,-4,.3,.3,-np.pi,0,-2,-.2,-.2],[4,4,8,8,np.pi,2,2,.2,.2])).x
        sizes=np.sort(p[2:4])*np.sqrt(8*np.log(2))*scan.GRID
        return dict(x_offset_px=p[0],y_offset_px=p[1],minor_fwhm_m=sizes[0],major_fwhm_m=sizes[1],amplitude_log=p[5])
    pd.DataFrame([dict(product=n,**fit(a)) for n,a in zip(ORDER[2:]+["median"],ratios+[m])]).to_csv(out/'widths.csv',index=False)
    radial=[]
    for lo,hi in [(0,2.5),(2.5,5),(5,8),(8,12),(12,20),(20,30),(30,45)]:
        def shell(rr):
            return np.mean(m[(rr>lo)&(rr<=hi)])-np.mean(m[(rr>46)&(rr<=60)])
        # Far-background annuli use only positions supported by the 193-pixel cutout.
        control=[shell(np.hypot(x-i,y-j)) for i in range(-36,37,12) for j in range(-36,37,12) if np.hypot(i,j)>hi+5]
        radial.append(dict(inner_px=lo,outer_px=hi,mean_log_change=shell(r),control_median=np.median(control) if control else np.nan,control_min=min(control) if control else np.nan,control_max=max(control) if control else np.nan,n_centers=len(control)))
    pd.DataFrame(radial).to_csv(out/'radial.csv',index=False)
    fig,axes=plt.subplots(2,6,figsize=(13.5,5.1),layout="constrained")
    for j,(im,date) in enumerate(zip(imgs,DATES)):
        for i,hw in enumerate([52,10]):
            ax=axes[i,j];pix=im[mid-hw:mid+hw+1,mid-hw:mid+hw+1]
            b=np.mean(im[(r>6)&(r<12)])
            ax.imshow(pix/b,cmap="gray",interpolation="nearest",vmin=.89 if i==0 else .96,vmax=1.17 if i==0 else 1.17);ax.axis("off")
            if i==0:
                ax.set_title(date,fontsize=12);ax.plot([hw,hw],[hw-17,hw-9],color='turquoise',lw=1);ax.plot([hw+9,hw+17],[hw,hw],color='turquoise',lw=1)
            if j==0:
                length=20 if i==0 else 5
                ax.plot([2,2+length/scan.GRID],[2*hw-3]*2,color='white',lw=2)
                ax.text(2,2*hw-4,f"{length} m",color='white',fontsize=8)
    fig.suptitle("Emergence of a bright marking on the lunar farside",fontsize=17)
    fig.savefig(out/'chronology.png',dpi=150,bbox_inches='tight');plt.close(fig)
    print(pd.DataFrame(rows).round(5).to_string(index=False))
    print(fit(m));print(pd.DataFrame(radial).round(5).to_string(index=False))

if __name__=="__main__":calc(Path(sys.argv[1]),Path(sys.argv[2]))
