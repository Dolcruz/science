"""Reproject and tie opposite-Sun NAC frames to the stereo-mosaic grid."""
from field import *
import re
import requests

IDS=["M1307882452LC","M1540060927RC","M1538900584LC","M1404174663LC"]
COMPANIONS=["M1538900584RC","M1540060927LC"]
def request_bytes(name,start,end,url):
    folder=DATA/"ranges";folder.mkdir(exist_ok=True,parents=True)
    path=folder/f"{name}-{start}-{end}"
    if not path.exists():
        r=requests.get(url,headers={"Range":f"bytes={start}-{end}"})
        r.raise_for_status()
        assert r.headers.get("Content-Range","").startswith(f"bytes {start}-{end}/") and len(r.content)==end-start+1
        path.write_bytes(r.content)
    return path.read_bytes()

def archive_grid(name,m):
    margin=220
    xx,yy=np.meshgrid(np.arange(-margin,N+margin),np.arange(-margin,N+margin))
    lon,lat=forward_map(xx,yy)
    ul,ur,ll,lr=np.asarray(m["corners"])
    inv=np.linalg.inv(np.column_stack([ur-ul,ll-ul])); cr=lr-ll-ur+ul
    x,y=lon-ul[0],lat-ul[1];a,b=inv[0,0]*x+inv[0,1]*y,inv[1,0]*x+inv[1,1]*y
    for _ in range(4):
        t=a*b
        a=inv[0,0]*(x-cr[0]*t)+inv[0,1]*(y-cr[1]*t)
        b=inv[1,0]*(x-cr[0]*t)+inv[1,1]*(y-cr[1]*t)
    px,py=(a*(m["samples"]-1)).astype("f4"),(b*(m["lines"]-1)).astype("f4")
    header=request_bytes(name,0,8191,m["original"])
    field=lambda k:int(re.search(rb"^\s*"+re.escape(k)+rb"\s*=\s*(\d+)",header,re.M)[1])
    offset=(field(b"^IMAGE")-1)*field(b"RECORD_BYTES")
    h,w=m["lines"],m["samples"];y0=max(0,int(py.min())-2);y1=min(h,int(py.max())+4)
    block=request_bytes(name,offset+2*w*y0,offset+2*w*y1-1,m["original"])
    raw=np.frombuffer(block,"<i2").reshape(-1,w).astype("f4")
    # The calibrated signed I/F data retain very low genuine values in
    # grazing illumination. Only negative detector codes are treated as null.
    raw[raw<0]=0
    return cv2.remap(raw,px,py-y0,cv2.INTER_LINEAR),margin

def ties(arr,ref,margin,reverse):
    def normalized(img):
        q=img[img>0];a=np.log(np.maximum(img,np.percentile(q,1)))
        h=a-blur(a,8)
        return h/np.maximum(.03,blur(abs(h),12))
    ref_z=normalized(ref);arr_z=normalized(arr)
    sift=cv2.SIFT_create(contrastThreshold=.025)
    positions=[];dest=[]
    for mode in ("signed","edges"):
        def desc(z):
            if mode=="edges":
                gy,gx=np.gradient(blur(z,1));v=np.hypot(gy,gx)
                im=np.uint8(np.clip(v*75,0,255))
            else:im=np.uint8(np.clip(128+z*39,0,255))
            return sift.detectAndCompute(im,None)
        pts,d=desc(-arr_z if (reverse and mode=="signed") else arr_z);qr,e=desc(ref_z)
        match=cv2.BFMatcher().knnMatch(d,e,k=2)
        for u,v in match:
            if u.distance>.83*v.distance:continue
            p=np.array(pts[u.queryIdx].pt)-margin;q=np.array(qr[u.trainIdx].pt)
            if np.max(abs(p-q))>230 or np.linalg.norm(q-600)<260:continue
            positions.append(p);dest.append(q)
    # Low-Sun shadow boundaries reverse across depressions, suppressing SIFT
    # descriptors. Spatially distributed patch matches on unsigned relief
    # retain the locations of the surrounding old craters under both Suns.
    def structural(z):
        g=blur(z,1)
        gy,gx=np.gradient(g)
        return cv2.resize(blur(np.hypot(gx,gy),2),None,fx=.25,fy=.25,interpolation=cv2.INTER_AREA)
    aa,bb=structural(arr_z),structural(ref_z)
    for y in range(96,N-95,96):
        for x in range(96,N-95,96):
            if np.hypot(x-600,y-600)<285:continue
            qx,qy=x//4,y//4
            p=bb[qy-15:qy+16,qx-15:qx+16]
            sx,sy=qx+margin//4,qy+margin//4
            k=margin//4-1
            region=aa[sy-k:sy+k+1,sx-k:sx+k+1]
            match=cv2.matchTemplate(region,p,cv2.TM_CCOEFF_NORMED)
            by,bx=np.unravel_index(match.argmax(),match.shape)
            if match[by,bx]<.32:continue
            px=4*(sx-k+bx+15)-margin
            py=4*(sy-k+by+15)-margin
            positions.append([px,py]);dest.append([x,y])
    src,dst=np.float32(positions),np.float32(dest)
    if len(src)<5:return None,None
    mat,ok=cv2.estimateAffine2D(src,dst,ransacReprojThreshold=4.)
    if mat is None or ok.sum()<6 or np.linalg.det(mat[:,:2])<=0 or np.max(abs(mat[:,:2]-np.eye(2)))>.12:return None,None
    rr=np.linalg.norm(src@mat[:,:2].T+mat[:,2]-dst,axis=1)
    use=ok[:,0]>0;held=src[use]
    adj=mat.copy();adj[:,2]-=mat[:,:2]@np.array([margin,margin])
    z=cv2.warpAffine(arr,adj,(N,N))
    stats=dict(ties=int(use.sum()),median_error=float(np.median(rr[use])),p95_error=float(np.percentile(rr[use],95)),spans=(held.max(axis=0)-held.min(axis=0)).tolist(),affine=mat.tolist())
    return z,stats

def main():
    inputs=json.loads((D/"extra-observations.json").read_text())
    reg=np.load(D/"registered.npz")
    extra={};st={}
    for name,m in inputs.items():
        arr,margin=archive_grid(name,m)
        reverse=name in IDS[:2] or name==COMPANIONS[1]
        which="pre10" if reverse else ("postH" if name==IDS[2] or name==COMPANIONS[0] else "pre18")
        z,stats=ties(arr,reg[which],margin,reverse)
        print(name,stats,flush=True)
        if z is not None:
            extra[name]=z; st[name]=stats
    np.savez_compressed(D/"additional.npz",**extra);(D/"additional-registration.json").write_text(json.dumps(st,indent=2))
if __name__=="__main__":
    with threadpool_limits(limits=4):main()
