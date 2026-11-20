"""Rank each detection after fitting local brightness, texture and slope gradients off target."""
import argparse,math
from pathlib import Path
import numpy as np,pandas as pd,cv2
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
from threadpoolctl import threadpool_limits
from matplotlib import colormaps

def assess(a,b,sign,sigma):
    smooth=lambda v,s:cv2.GaussianBlur(v,(0,0),s)
    loga=np.log(np.maximum(a,100))
    ratio=np.log(np.maximum(b,100))-loga
    low=smooth(loga,1);gy,gx=np.gradient(low)
    X=np.stack([np.ones_like(a),gx,gy,low-np.median(low),low-smooth(low,3),low-smooth(low,9),gx*gx+gy*gy],axis=-1)
    yy,xx=np.indices(a.shape);r=np.hypot(xx-32,yy-32)
    ann=(r>=13)&(r<=29)&(a>100)&(b>100)
    if ann.sum()<120:
        return np.nan,np.nan,ratio
    design=X[ann];y=ratio[ann];w=np.ones(len(y))
    for _ in range(4):
        coef=np.linalg.lstsq(design*w[:,None],y*w,rcond=None)[0]
        delta=y-design@coef
        w=np.sqrt(np.minimum(1,1.5*np.median(abs(delta-np.median(delta)))/.6745/np.maximum(abs(delta),.0001)))
    residual=ratio-X@coef;filt=smooth(residual,sigma)
    center=np.s_[30:35,30:35]
    v=np.max(sign*filt[center]);scatter=max(.005,1.48*np.median(abs(filt[ann]-np.median(filt[ann]))))
    return v,v/scatter,residual

def sheet(batch,cuts,out):
    width=195;h=86;ncol=5;size=63
    page=Image.new('RGB',(width*ncol,h*math.ceil(len(batch)/ncol)),'white');d=ImageDraw.Draw(page)
    for t,r in enumerate(batch.itertuples()):
        x=t%ncol*width;y=t//ncol*h
        a,b=cuts[r.chip];_,_,res=assess(a,b,r.sign,r.sigma)
        for col,v in enumerate([a,b,res]):
            crop=v[8:-8,8:-8]
            if col<2:
                lo,hi=np.percentile(crop,[1,99]);rgb=Image.fromarray(np.uint8(np.clip((crop-lo)/(hi-lo),0,1)*255))
            else:rgb=Image.fromarray(colormaps['RdBu_r'](np.clip(.5+crop/.25,0,1),bytes=True)[:,:,:3])
            page.paste(rgb.resize((size,size),Image.Resampling.NEAREST),(x+col*size,y+14))
        d.text((x,y),f'{r.rank}  {r.x},{r.y}  {r.corrected*r.sign:+.2f}',fill='black')
    page.save(out,quality=89)

def main(p, render_all=False):
    f=pd.read_csv(p/'peaks.csv');cuts=np.load(p/'cutouts.npz')
    if not len(f):return
    f['corrected'],f['local_score']=zip(*(assess(*cuts[r.chip],r.sign,r.sigma)[:2] for r in f.itertuples()))
    f.sort_values('corrected',ascending=False,inplace=True,ignore_index=True)
    xy=f[['x','y']].to_numpy();tree=cKDTree(xy);removed=set();chosen=[]
    for i,point in enumerate(xy):
        if i in removed:continue
        chosen.append(i);removed.update(tree.query_ball_point(point,8))
    f=f.iloc[chosen].copy();f.insert(0,'rank',np.arange(1,len(f)+1));f.to_csv(p/'ranked.csv',index=False)
    for i in range(0,len(f) if render_all else min(len(f),40),40):
        sheet(f.iloc[i:i+40],cuts,p/f'locations-{i//40+1:02d}.jpg')
    print(len(f), 'distinct locations')

if __name__=='__main__':
    cv2.setNumThreads(4)
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path)
    p.add_argument('--all-sheets', action='store_true', help='Render contact sheets for every ranked detection')
    args=p.parse_args()
    with threadpool_limits(4,'blas'):main(args.folder,args.all_sheets)
