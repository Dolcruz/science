"""Locate the site's surroundings on JAXA's independently projected Kaguya TC mosaics."""
from survey import setup,scan
from pathlib import Path
import cv2,json,sys,requests
import numpy as np
import pandas as pd
setup()
LON,LAT=226.05,-7.658
PPD=4096
def fetch(mode,root):
    stem="TCO_MAP"+('m' if mode=='morning' else 'e')+"04_S06E225S09E228SC"
    url=f"https://data.darts.isas.jaxa.jp/pub/pds3/sln-l-tc-5-{mode}-map-v4.0/lon225/data/{stem}"
    cache=root/'kaguya';cache.mkdir(exist_ok=True)
    label=cache/(stem+'.lbl')
    if not label.exists():
        r=requests.get(url+'.lbl');r.raise_for_status();label.write_bytes(r.content)
    from re import search
    txt=label.read_text()
    assert 'MSB_UNSIGNED_INTEGER' in txt and int(search(r'LINE_SAMPLES\s*=\s*(\d+)',txt)[1])==12288
    cy=round((-6-LAT)*PPD);cx=round((LON-225)*PPD);h=300;w=12288
    lo=(cy-h)*w*2;hi=(cy+h+1)*w*2
    stored=cache/(stem+f".{lo}-{hi}.rows")
    if not stored.exists():
        with requests.get(url+'.img',headers={'Range':f'bytes={lo}-{hi-1}'},stream=True) as r:
            r.raise_for_status()
            if r.status_code==206:
                if not r.headers['Content-Range'].startswith(f'bytes {lo}-{hi-1}/'):raise ValueError('Unexpected content range')
                block=r.content
            elif r.status_code==200:
                # Some DARTS servers serve a full PDS image even for a Range request.
                parts=[];position=0
                for chunk in r.iter_content(1024*1024):
                    end=position+len(chunk)
                    if end>lo and position<hi:parts.append(chunk[max(0,lo-position):min(len(chunk),hi-position)])
                    position=end
                    if end>=hi:break
                block=b''.join(parts)
            else:raise ValueError('Unexpected response')
        if len(block)!=hi-lo:raise ValueError('Incomplete TC rows')
        stored.write_bytes(block)
    block=stored.read_bytes()
    chip=np.frombuffer(block,dtype='>u2').reshape(2*h+1,w)[:,cx-h:cx+h+1].astype('f4')
    return chip,cx-h,cy-h

def hp(im):
    v=np.log(np.maximum(im,100.))
    z=cv2.GaussianBlur(v,(0,0),.75)-cv2.GaussianBlur(v,(0,0),7)
    return z
def get_matches(im,center,kaguya):
    # Map the NAC tile onto a regular grid at the TC latitude/longitude sample spacing.
    ax=(scan.DEG*np.cos(np.deg2rad(LAT))/PPD)/scan.GRID;ay=(scan.DEG/PPD)/scan.GRID
    x=(np.arange(int(im.shape[1]/ax))*ax).astype('f4')
    y=(np.arange(int(im.shape[0]/ay))*ay).astype('f4')
    xx,yy=np.meshgrid(x,y);scaled=cv2.remap(cv2.GaussianBlur(im,(0,0),2.6),xx,yy,cv2.INTER_LINEAR)
    good=cv2.erode(np.uint8(scaled>100),np.ones((31,31),np.uint8)).astype(bool)
    nac=hp(scaled);tc=hp(kaguya)
    p=center/[ax,ay];src=[];dst=[];scores=[]
    # Every template is centered at least 21 TC pixels (about 154 m) from the marking.
    for py in range(20,len(y)-20,16):
        for px in range(20,len(x)-20,16):
            if np.linalg.norm(p-[px,py])<21 or not good[py,px]:continue
            h=15;template=nac[py-h:py+h+1,px-h:px+h+1];delta=np.array([px,py])-p
            # Search near the nominal chip center with a margin >1 km.
            gx=int(round(300+delta[0]));gy=int(round(300+delta[1]))
            x0=max(0,gx-140-h);x1=min(tc.shape[1],gx+140+h+1)
            y0=max(0,gy-140-h);y1=min(tc.shape[0],gy+140+h+1)
            m=cv2.matchTemplate(tc[y0:y1,x0:x1],template,cv2.TM_CCOEFF_NORMED)
            _,v,_,(u,w)=cv2.minMaxLoc(m)
            if v<.45:continue
            src.append([px,py]);dst.append([u+x0+h,w+y0+h]);scores.append(v)
    if len(src)<6:return
    src,dst=np.array(src,dtype='f4'),np.array(dst,dtype='f4')
    mat,mask=cv2.estimateAffine2D(src,dst,ransacReprojThreshold=1.9)
    if mat is None:return
    keep=mask.ravel().astype(bool)
    if keep.sum()<8 or np.max(abs(np.linalg.svd(mat[:,:2],compute_uv=False)-1))>.10:return
    q=mat[:,:2]@p+mat[:,2]
    # Independent spatial check. Even/odd columns of search templates alternate.
    checks=[]
    for k in [0,1]:
        parity=((src[:,0].astype(int)-20)//16)%2==k
        if (keep&parity).sum()<3 or (keep&~parity).sum()<3:return
        design=np.column_stack([src,np.ones(len(src))])
        coef=np.linalg.lstsq(design[keep&parity],dst[keep&parity],rcond=None)[0]
        e=np.linalg.norm(design[keep&~parity]@coef-dst[keep&~parity],axis=1)
        checks.extend(e.tolist())
    return q,int(keep.sum()),float(np.median(np.array(scores)[keep])),float(np.quantile(checks,.9)),float(np.linalg.norm(src[keep]-p,axis=1).min())
def run(root,out):
    points=dict(np.load(root/'terrain/cross-sun-centers.npz'))
    rows=[]
    for mode in ['morning','evening']:
        m,x0,y0=fetch(mode,root)
        for n,p in points.items():
            r=get_matches(np.load(root/'tiles'/(n+'.npy')),p,m)
            if r is None:continue
            q,count,ncc,e90,nearest=r
            lon=225+(q[0]+x0)/PPD;lat=-6-(q[1]+y0)/PPD
            rows.append(dict(mode=mode,product=n,longitude=lon,latitude=lat,ties=count,median_ncc=ncc,p90_heldout_px=e90,nearest_offtarget_px=nearest))
            print(mode,n,count,round(lon,7),round(lat,7),round(e90,2),round(ncc,2),flush=True)
    pd.DataFrame(rows).to_csv(out/'kaguya-locations.csv',index=False)
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
