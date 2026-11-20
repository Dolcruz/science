"""Measure spatially resolved differences under matched eastward or westward sunlight."""
from images import *
import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import least_squares
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
PAIRS=[
 ("M1124130817LC","M1481346260RC"),
 ("M114498484RC","M1509446289RC"),
 ("M1335882808RC","M1524669573LC"),
 ("M1398120658RC","M1512968740RC"),
 ("M1398120658RC","M1500081055LC"),
 ("M1385218373RC","M1500081055LC"),
 ("M1385225417RC","M1515317029RC"),
 ("M1422745700LC","M1509446289RC")]
def run(root,loc,out):
    out.mkdir(parents=True,exist_ok=True);m=json.loads((root/'observations.json').read_text())
    coords=json.loads((loc/'centers.json').read_text())
    y,x=np.indices((151,151),dtype=float);x-=75;y-=75;r=np.hypot(x,y)
    names=sorted({n for pair in PAIRS for n in pair if n in coords});images={}
    for n in names:
        p=coords[n];tile=np.load(root/'tiles'/(n+'.npy'))
        images[n]=cv2.getRectSubPix(tile,(151,151),(p['x'],p['y']))
    outputs={};measure=[];polarity=[]
    usable=[pair for pair in PAIRS if all(n in images for n in pair)]
    fig,ax=plt.subplots(len(usable),3,figsize=(7.5,2.4*len(usable)),layout='constrained')
    for row,(old,new) in enumerate(usable):
        for a in ax[row]:a.set_axis_off()
        if old not in images or new not in images:continue
        a,b=[np.maximum(images[n]/np.median(images[n][(r<65)&(r>15)]),.025).astype(float) for n in [old,new]]
        # Suppress subpixel interpolation/PSF differences without erasing resolved relief.
        aa,bb=[gaussian_filter(np.log(v),.80) for v in [a,b]]
        mask=(r>=12)&(r<65)&(aa>-2.0)&(bb>-2.0)
        def warp(p):return map_coordinates(aa,[y+75+p[1],x+75+p[0]],order=1,mode='nearest')*p[2]+p[3]
        def fun(p):return (warp(p)-bb)[mask]
        sol=least_squares(fun,[.001,.001,1,0],loss='soft_l1',f_scale=.035,bounds=([-5,-5,.20,-1.5],[5,5,2.5,1.5]),diff_step=.001)
        before=warp(sol.x);d=bb-before;d-=gaussian_filter(d,12)
        # Kernel-smooth the background using the valid overlap only at swath boundaries.
        valid=(images[old]>100)&(images[new]>100)
        rawdiff=bb-before
        weight=gaussian_filter(valid.astype(float),12)
        d=rawdiff-gaussian_filter(rawdiff*valid,12)/np.maximum(weight,.01)
        outputs[old+'_'+new]=np.stack([before,bb,d])
        for label,cx,cy in [('marking',0,0),('northeast depression',1.5,-7),('southwest depression',-8,3.5)]:
            dx=x-cx;dy=y-cy;rr=np.hypot(dx,dy)
            east=(rr<=4.5)&(dx>=1);west=(rr<=4.5)&(dx<=-1)
            rowp=dict(before=old,after=new,location=label)
            for key,z in [('before',before),('after',bb),('difference',d)]:
                rowp[key+'_east_minus_west']=float(z[east].mean()-z[west].mean())
            polarity.append(rowp)
        def metrics(ix,iy):
            dx=x-ix;dy=y-iy;rr=np.hypot(dx,dy);k=rr<=5
            bg=np.median(d[(rr>=8)&(rr<=12)]);dd=d-bg
            return [dd[k].mean(),dd[k].min(),dd[k].max(),dd[k&(dx>0)].mean()-dd[k&(dx<0)].mean()]
        v=np.array(metrics(0,0));controls=np.array([metrics(ix,iy) for ix in range(-50,51,10) for iy in range(-50,51,10) if np.hypot(ix,iy)>=12 and weight[75+iy,75+ix]>.95])
        results={};names2=['mean','min','max','east_minus_west']
        for i,s in enumerate(names2):
            results[s]=v[i];results[s+'_control_pct']=100*np.mean(controls[:,i]<v[i])
        measure.append(dict(before=old,after=new,in1=m[old]['incidence_deg'],in2=m[new]['incidence_deg'],native_width1=m[old]['w_m'],native_width2=m[new]['w_m'],dx_px=sol.x[0],dy_px=sol.x[1],control_count=len(controls),**results))
        for j,arr in enumerate([before,bb,d]):
            a=ax[row,j];chip=arr[60:91,60:91]
            if j<2:q=np.percentile(np.concatenate([before[60:91,60:91],bb[60:91,60:91]]),[2,98]);a.imshow(chip,cmap='gray',vmin=q[0],vmax=q[1],interpolation='nearest')
            else:a.imshow(chip,cmap='RdBu_r',vmin=-.26,vmax=.26,interpolation='nearest')
            a.plot([15,15],[5,9],color='turquoise',lw=.9);a.plot([21,25],[15,15],color='turquoise',lw=.9)
            a.set_title((old+' '+str(m[old]['incidence_deg'])+'°',new+' '+str(m[new]['incidence_deg'])+'°','Change in log brightness')[j],fontsize=9)
    plt.savefig(out/'matched-light.png',dpi=135);plt.close(fig)
    np.savez_compressed(out/'matched-light.npz',**outputs)
    pd.DataFrame(polarity).to_csv(out/'neighboring-relief.csv',index=False)
    pd.DataFrame(measure).to_csv(out/'matched-light.csv',index=False)
    print(pd.DataFrame(measure).round(3).to_string(index=False))
if __name__=='__main__':run(*[Path(k) for k in sys.argv[1:]])
