"""Tie an image detector location to the LROC WMS stamp mosaic using off-target terrain."""
from pathlib import Path
import hashlib
import io
from urllib.request import urlopen
import cv2,numpy as np,pandas as pd
from PIL import Image
from threadpoolctl import threadpool_limits
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
import argparse
TARGET=np.array([864.,471.])
REF='M1148028911RC'
def prep(a):
    lo,hi=np.percentile(a[a>0],[.5,99.5])
    return np.uint8(np.clip((a-lo)/(hi-lo)*255,0,255))
def feat(im):
    return cv2.SIFT_create(contrastThreshold=.018).detectAndCompute(im,None)
def link(k,l,point,exclude):
    kp,d=k;lp,e=l
    good=[m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2) if m.distance<.78*n.distance]
    if len(good)<8:return
    src=np.float32([kp[v.queryIdx].pt for v in good]);dst=np.float32([lp[v.trainIdx].pt for v in good])
    _,ids=np.unique(np.round(src/4),axis=0,return_index=True);src,dst=src[ids],dst[ids]
    keep=np.linalg.norm(src-point,axis=1)>exclude;src,dst=src[keep],dst[keep]
    M,sel=cv2.estimateAffine2D(src,dst,ransacReprojThreshold=4)
    if M is None or sel.sum()<14:return
    sel=sel.ravel().astype(bool);x=src[sel];y=dst[sel];d=x-point
    hull=cv2.convexHull(x);dist=cv2.pointPolygonTest(hull,tuple(point),True)
    if dist<=0:return
    design=np.c_[np.ones(len(x)),d]
    w=np.exp(-.5*np.sum(d*d,axis=1)/240**2)
    coeff=np.linalg.lstsq(design*w[:,None]**.5,y*w[:,None]**.5,rcond=None)[0]
    err=np.linalg.norm(design@coeff-y,axis=1)
    return coeff[0],len(src),len(x),float(np.median(err)),float(dist)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tile_directory', type=Path, help='North-up NAC arrays regenerated with reconstructed/tiles.py')
    parser.add_argument('--map',type=Path,help='Use a previously downloaded WMS PNG')
    args=parser.parse_args()
    TILES=args.tile_directory
    cv2.setNumThreads(4)
    with threadpool_limits(4,'blas'):
        # Both the PDS tiles and the WMS geographic GetMap have north at the top.
        if args.map:
            raster=args.map.read_bytes()
        else:
            with urlopen((HERE/'wms.url').read_text().strip()) as response:
                raster=response.read()
        digest=hashlib.sha256(raster).hexdigest()
        print('WMS image SHA-256:',digest)
        if digest!='650b36c863453e52b4ec877c0bd27c58ef56af2024490f1fe9ba986e4ccd0076':
            print('The server image differs from the image used for the published tie positions.')
        sky=np.array(Image.open(io.BytesIO(raster)).convert('L'))
        if sky.shape!=(1600,1600):
            raise ValueError(f'Expected a 1600 by 1600 WMS map, received {sky.shape}')
        wf=feat(prep(sky));rf=feat(prep(np.load(TILES/(REF+'.npy'))))
        rows=[]
        for f in TILES.glob('*.npy'):
            ff=feat(prep(np.load(f)))
            centers=np.load(HERE/'cross-sun-centers.npz')
            if f.stem in centers:pt=centers[f.stem];ns=0;er=0
            else:
                one=link(rf,ff,TARGET,40)
                if one is None:continue
                pt,_,ns,er,_=one
            out=link(ff,wf,pt,40)
            print(f.stem,'map',None if out is None else out[2],flush=True)
            if out is None:continue
            q,_,n,me,hu=out
            lon=-133.94415-.085/2+(q[0]+.5)*.085/1600
            lat=-7.65815+.085/2-(q[1]+.5)*.085/1600
            rows.append(dict(name=f.stem,lon_e=lon%360,lat=lat,pixel_x=q[0],pixel_y=q[1],
                        source_ties=ns,map_ties=n,source_error_px=er,map_error_px=me,hull_margin_source_px=hu))
            print(rows[-1],flush=True)
        pd.DataFrame(rows).to_csv(HERE/'ties.csv',index=False)
