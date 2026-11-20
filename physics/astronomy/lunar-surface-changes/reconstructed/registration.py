"""Search overlapping calibrated LROC images for compact surface changes."""
import math
import re
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Polygon, box

META = {}
GRID = 1.05
CORE = 896
PAD = 224
FULL = CORE + 2*PAD
DEG = np.deg2rad(1)*1737400
ORIGIN = np.array([225.97095, -7.30832])
SCALE = np.array([DEG*np.cos(np.deg2rad(ORIGIN[1])), -DEG])
cv2.setNumThreads(4)


class Frame:
    def __init__(self, name, folder):
        self.name = name
        meta = META[name]
        self.vertices = (np.asarray(meta["corners"]) - ORIGIN) * SCALE / GRID
        self.footprint = Polygon(self.vertices[[0,1,3,2]])
        path = folder/(name+".IMG")
        with path.open("rb") as f:
            label = f.read(10000).decode("latin1")
        def value(key):
            return int(re.search(r"^\s*"+re.escape(key)+r"\s*=\s*(\d+)",label,re.M).group(1))
        offset = (value("^IMAGE") - 1)*value("RECORD_BYTES")
        self.h, self.w = meta["lines"], meta["samples"]
        self.image = np.memmap(path, dtype="<i2", mode="r", offset=offset, shape=(self.h,self.w))

    def native(self, east, south):
        ul,ur,ll,lr = self.vertices
        inv = np.linalg.inv(np.column_stack([ur-ul,ll-ul]))
        cross = lr-ll-ur+ul
        x,y = east-ul[0],south-ul[1]
        a,b = inv[0,0]*x+inv[0,1]*y, inv[1,0]*x+inv[1,1]*y
        for _ in range(4):
            prod = a*b
            a = inv[0,0]*(x-cross[0]*prod)+inv[0,1]*(y-cross[1]*prod)
            b = inv[1,0]*(x-cross[0]*prod)+inv[1,1]*(y-cross[1]*prod)
        return a*(self.w-1), b*(self.h-1)

    def tile(self, i, j):
        # Evaluate the smooth corner model on a grid and interpolate coordinates.
        # One extra cell on each side preserves the edge derivatives.
        step = 32
        v = np.arange(-step,FULL+step,step)+(step-1)/2-PAD
        x,y = np.meshgrid(i*CORE+v, j*CORE+v)
        a,b = self.native(x,y)
        def expand(arr):
            z=cv2.resize(arr.astype("float32"),(FULL+2*step,FULL+2*step),interpolation=cv2.INTER_LINEAR)
            return z[step:-step,step:-step].copy()
        a,b=expand(a),expand(b)
        x0=max(0,int(np.floor(a.min()))-1);x1=min(self.w,int(np.ceil(a.max()))+2)
        y0=max(0,int(np.floor(b.min()))-1);y1=min(self.h,int(np.ceil(b.max()))+2)
        if x0>=x1 or y0>=y1:
            return np.zeros(a.shape,np.float32)
        chip=self.image[y0:y1,x0:x1].astype("float32")
        chip[chip<=100]=0
        return cv2.remap(chip,a-x0,b-y0,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)


def display(a):
    small=a[::5,::5]
    valid=small[small>100]
    if len(valid)<10:
        return np.zeros(a.shape,"uint8")
    lo,hi=np.percentile(valid,[1,99])
    return np.clip((a-lo)*(255/max(hi-lo,1)),0,255).astype("uint8")


def describe(a):
    half=cv2.resize(a,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
    return cv2.SIFT_create().detectAndCompute(display(half),np.uint8(half>100)*255)


def align(moving, fixed, fixed_desc, auxiliary=None):
    kp,ds=describe(moving)
    if ds is None or fixed_desc[1] is None or min(len(ds),len(fixed_desc[1]))<3:
        return None
    matches=cv2.BFMatcher().knnMatch(ds,fixed_desc[1],k=2)
    good=[a for a,b in matches if a.distance<.75*b.distance]
    if len(good)<12:
        return None
    src=np.float32([kp[m.queryIdx].pt for m in good])*2+.5
    dst=np.float32([fixed_desc[0][m.trainIdx].pt for m in good])*2+.5
    mat,mask=cv2.estimateAffine2D(src,dst,ransacReprojThreshold=3)
    if mat is None or mask.sum()<12 or np.max(abs(np.linalg.svd(mat[:,:2],compute_uv=False)-1))>.18 or np.linalg.det(mat[:,:2])<0:
        return None
    inliers=mask.ravel().astype(bool)
    affine_error=np.linalg.norm(src @ mat[:,:2].T+mat[:,2]-dst,axis=1)
    basic=cv2.warpAffine(moving,mat,(FULL,FULL))
    # Thin-plate/local terrain parallax can exceed a single pixel. Nearby tie
    # displacements from independent terrain interest points correct it smoothly.
    first=display(fixed); second=display(basic)
    cells=64; n=FULL//cells
    coords=cv2.goodFeaturesToTrack(first,0,.025,8,mask=np.uint8((fixed>100)&(basic>100))*255,blockSize=5)
    if coords is None or len(coords)<10:
        return None
    new,st,err=cv2.calcOpticalFlowPyrLK(first,second,coords,None,winSize=(25,25),maxLevel=2)
    back,sb,_=cv2.calcOpticalFlowPyrLK(second,first,new,None,winSize=(25,25),maxLevel=2)
    ok=(st.ravel()>0)&(sb.ravel()>0)&(np.linalg.norm((back-coords)[:,0],axis=1)<.65)
    disp=(new-coords)[:,0];ok&=(np.linalg.norm(disp,axis=1)<12)
    points=coords[ok,0];delta=disp[ok]
    if len(points)<10:
        return None
    ids=(points[:,1].astype(int)//cells)*n+points[:,0].astype(int)//cells
    offsets=np.full((n*n,2),np.nan,'f4')
    order=np.argsort(ids)
    for arr in np.split(order,np.flatnonzero(np.diff(ids[order]))+1):
        if len(arr)>=3:
            offsets[ids[arr[0]]]=np.median(delta[arr],axis=0)
    offsets=offsets.reshape(n,n,2)
    missing=~np.isfinite(offsets[:,:,0])
    if missing.all():return None
    nearest=distance_transform_edt(missing,return_distances=False,return_indices=True)
    offsets=offsets[tuple(nearest)]
    smooth=cv2.resize(offsets,(FULL,FULL),interpolation=cv2.INTER_LINEAR)
    y,x=np.indices((FULL,FULL),dtype='f4')
    out=cv2.remap(basic,x+smooth[:,:,0],y+smooth[:,:,1],cv2.INTER_LINEAR)
    diagnostics=dict(ties=int(inliers.sum()),median_error=float(np.median(affine_error[inliers])),
                     local_ties=len(points))
    if auxiliary is not None:
        aux=cv2.warpAffine(auxiliary,mat,(FULL,FULL))
        return out,diagnostics,cv2.remap(aux,x+smooth[:,:,0],y+smooth[:,:,1],cv2.INTER_LINEAR)
    return out,diagnostics


def scores(before, after):
    valid=(before>100)&(after>100)
    # Keep the support of the background filter away from the chip edge.
    valid=cv2.erode(valid.astype("uint8"),np.ones((75,75),'u1')).astype(bool)
    log_ratio=np.log(np.maximum(after,100))-np.log(np.maximum(before,100))
    def blur(a,s):return cv2.GaussianBlur(a,(0,0),s)
    residual=log_ratio-blur(log_ratio,18)
    layers=[]
    for sigma in [2,5]:
        layer=blur(residual,sigma)
        noise=np.maximum(.005,1.2533*blur(abs(layer),25))
        layers.append((sigma,layer,layer/noise))
    return valid,layers


def scan_pair(before,after,out):
    label=before.name
    overlap=before.footprint.intersection(after.footprint)
    bounds=overlap.bounds
    tiles=[(i,j) for j in range(math.floor(bounds[1]/CORE)-1,math.ceil(bounds[3]/CORE)+1)
           for i in range(math.floor(bounds[0]/CORE)-1,math.ceil(bounds[2]/CORE)+1)
           if overlap.buffer(PAD).intersects(box(i*CORE,j*CORE,(i+1)*CORE,(j+1)*CORE))]
    print(label,"tiles",len(tiles),flush=True)
    records=[];tops=[];masks={}
    inner=np.s_[PAD:PAD+CORE,PAD:PAD+CORE]
    for n,(i,j) in enumerate(tiles):
        a,b=before.tile(i,j),after.tile(i,j)
        reg=align(a,b,describe(b))
        row=dict(i=i,j=j,valid=0,ties=0,median_error=np.nan,local_ties=0)
        if reg is not None:
            a,stats=reg
            valid,layers=scores(a,b)
            local=valid[inner]
            masks[f"{i}_{j}"]=np.packbits(local)
            row.update(stats,valid=int(local.sum()))
            if valid[FULL//2-105:FULL//2+105,FULL//2-105:FULL//2+105].all() and ((i+3*j)%8==0 or (i,j) in [(-1,0),(0,0)]):
                cut=np.s_[FULL//2-105:FULL//2+105,FULL//2-105:FULL//2+105]
                np.savez_compressed(out/"validation"/f"{label}_{i}_{j}.npz",before=a[cut],after=b[cut],valid=valid[cut],grid_m=GRID)
            for sigma,layer,zscore in layers:
                for sign in (-1,1):
                    amp=layer*sign
                    # Compact peaks in log reflectance, separately for both polarities.
                    maxima=cv2.dilate(amp,np.ones((21,21),"u1"))
                    picked=(amp>=maxima)&valid&(amp>=.035)&(sign*zscore>=3.5)
                    ys,xs=np.where(picked[inner])
                    for y,x in zip(ys,xs):
                        px=x+i*CORE;py=y+j*CORE
                        tops.append(dict(i=i,j=j,x=px,y=py,sigma=sigma,sign=sign,
                                         amp=float(amp[y+PAD,x+PAD]),z=float(sign*zscore[y+PAD,x+PAD])))
        records.append(row)
        if n%20==0:
            print(label,n+1,"/",len(tiles),"area km2",round(sum(r["valid"] for r in records)*GRID**2/1e6,2),flush=True)
    pd.DataFrame(records).to_csv(out/f"{label}-tiles.csv",index=False)
    pd.DataFrame(tops,columns="i j x y sigma sign amp z".split()).to_csv(out/f"{label}-peaks.csv",index=False)
    np.savez_compressed(out/f"{label}-masks.npz",**masks)
