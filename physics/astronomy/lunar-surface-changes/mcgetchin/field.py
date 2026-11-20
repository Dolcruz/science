"""Measure topography and time-variable crater-like shading around McGetchin."""
import os
for variable in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[variable]="4"
from pathlib import Path
import json
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from scipy.spatial import cKDTree
from scipy.ndimage import maximum_filter
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
cv2.setNumThreads(4)
D=Path(__file__).resolve().parent
DATA=Path(os.environ.get("MCGETCHIN_DATA",D/"data"))
X0,Y0=-3421266.,41646.
N=1200
Y,X=np.mgrid[:N,:N].astype("f4")
R=np.hypot(X-600,Y-600)
NAMES={"pre10":"M146540098LR_32bit.tif","pre18":"M1273794308R_32bit.tif",
       "postH":"M1523687730LR_32bit.tif","postM":"M1521345601L_32bit.tif",
       "postA":"M1519004052LR_32bit.tif","ortho":"NAC_DTM_NEW200CRAT3_M1521352616_100cm_crop.tif",
       "dtm":"NAC_DTM_NEW200CRAT3_E014N0671_crop.tif"}
def geotiff(name):
    im=Image.open(DATA/NAMES.get(name, name)); a=np.asarray(im).astype("f4")
    step=im.tag_v2[33550][0];x,y=im.tag_v2[33922][3:5]
    xx=(X0+X+.5-x)/step-.5;yy=(y-(Y0-Y-.5))/step-.5
    a[~np.isfinite(a)|(a<-9999)]=0
    return cv2.remap(a,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
def blur(a,s): return cv2.GaussianBlur(a,(0,0),s)
def log(a): return np.log(np.maximum(a,.001))
def high(a):
    z=log(a)
    return z-blur(z,16)
def texture(a):
    h=high(a)
    return h/np.maximum(blur(abs(h),16),.015)
def illumination(a,dtm):
    dy,dx=np.gradient(blur(dtm,3))
    h=high(a)
    mask=(R>330)&(X>40)&(Y>40)&(X<N-40)&(Y<N-40)
    idx=np.s_[::3,::3];m=mask[idx]
    w=np.c_[dx[idx][m],dy[idx][m],np.ones(m.sum())]
    beta=np.linalg.lstsq(w,h[idx][m],rcond=None)[0]
    return beta[:2]/np.linalg.norm(beta[:2])
def reg(a,b,sign=1,return_flow=False):
    ta,tb=texture(a)*np.float32(sign),texture(b)
    tie=[]
    for y in range(64,N-63,64):
        for x in range(64,N-63,64):
            if (x-600)**2+(y-600)**2<280**2: continue
            src=ta[y-52:y+53,x-52:x+53];template=tb[y-38:y+39,x-38:x+39]
            corr=cv2.matchTemplate(src,template,cv2.TM_CCOEFF_NORMED)
            py,px=np.unravel_index(corr.argmax(),corr.shape)
            if not (0<px<corr.shape[1]-1 and 0<py<corr.shape[0]-1 and corr[py,px]>.45):continue
            def sub(u,v,w):return float(.5*(u-w)/(u-2*v+w))
            tie.append([x,y,px-14+sub(*corr[py,px-1:px+2]),py-14+sub(*corr[py-1:py+2,px]),corr[py,px]])
    tie=np.asarray(tie)
    if len(tie)<4:
        out=(a,dict(count=len(tie)))
        return (*out,np.zeros((N,N,2),"f4")) if return_flow else out
    xy=tie[:,:2];offset=tie[:,2:4]
    pos=np.arange(16,N+32,32)
    xx,yy=np.meshgrid(pos,pos)
    idx=cKDTree(xy).query(np.c_[xx.ravel(),yy.ravel()],k=min(9,len(tie)))[1]
    grid=np.median(offset[idx],axis=1).reshape(*xx.shape,2).astype('f4')
    interpolate=cv2.remap(grid,(X-16)/32,(Y-16)/32,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    aligned=cv2.remap(a,X+interpolate[:,:,0],Y+interpolate[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    out=(aligned,dict(count=len(tie),median_displacement=np.median(offset,axis=0).tolist(),median_corr=float(np.median(tie[:,4]))))
    return (*out,interpolate) if return_flow else out

def load():
    d={k:geotiff(k) for k in NAMES}; dtm=d["dtm"]
    light={k:illumination(a,dtm) for k,a in d.items() if k!="dtm"}
    regs={}
    for k in ("pre10","pre18","postH","postM","postA"):
        sign=np.sign(np.dot(light[k],light["ortho"]))
        d[k],regs[k]=reg(d[k],d["ortho"],sign)
    return d,light,regs

def forward_map(X,Y):
    d=np.pi/180*1737400
    return (180+(X0+np.asarray(X)+.5)/(d*np.cos(np.deg2rad(1.))),(Y0-np.asarray(Y)-.5)/d)

def main():
    d,l,r=load()
    print({k:v.tolist() for k,v in l.items()},r,flush=True)
    (D/"registration.json").write_text(json.dumps({"geometry":r,"brightness_gradient_directions":{k:v.tolist() for k,v in l.items()}},indent=2))
    out={k:v for k,v in d.items()}
    np.savez_compressed(D/"registered.npz",**out)
    fig,axs=plt.subplots(2,3,figsize=(12,8))
    for ax,k in zip(axs.flat,("pre10","pre18","postH","postM","postA","dtm")):
        a=d[k];mask=(R>220) if k=='dtm' else (a>.005)&(R>220)
        ax.imshow(a,cmap='gray',vmin=np.percentile(a[mask],2),vmax=np.percentile(a[mask],98),extent=[-600,600,-600,600]);ax.set_title(k)
    fig.tight_layout();fig.savefig(D/"overview.png",dpi=130);plt.close(fig)
if __name__=="__main__":
    with threadpool_limits(limits=4): main()
