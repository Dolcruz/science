"""Pixel centers in distributed map products and original PDS detector arrays."""
from field import *
from opposite import IDS,COMPANIONS
SITES={"NW":(229,360),"NNE":(665,359),"old_pit_control":(237,390)}
def raw_pixel(x,y,meta):
    ul,ur,ll,lr=np.asarray(meta['corners']);lon,lat=forward_map(x,y)
    inv=np.linalg.inv(np.column_stack([ur-ul,ll-ul]));cross=lr-ll-ur+ul
    uv=inv@(np.array([lon,lat])-ul)
    for _ in range(4):uv=inv@(np.array([lon,lat])-ul-np.prod(uv)*cross)
    return uv*(np.array([meta['samples'],meta['lines']])-1)
def main():
    images={k:geotiff(k) for k in NAMES}; rows=[]
    for name,a in images.items():
        if name in ('dtm','ortho'):flow=None
        else:_,_,flow=reg(a,images['ortho'],return_flow=True)
        im=Image.open(DATA/NAMES[name]);step=im.tag_v2[33550][0];xm,ym=im.tag_v2[33922][3:5]
        for k,(x,y) in SITES.items():
            xx,yy=np.array([x,y])+(flow[y,x] if flow is not None else 0)
            sample=(X0+xx+.5-xm)/step-.5;line=(ym-Y0+yy+.5)/step-.5;lon,lat=forward_map(x,y)
            rows.append(dict(site=k,product=NAMES[name],kind='Zenodo GeoTIFF',east_deg=lon,north_deg=lat,sample=sample,line=line))
    ext=np.load(D/'additional.npz');regd=np.load(D/'registered.npz')
    inputs=json.loads((D/'extra-observations.json').read_text());stats=json.loads((D/'additional-registration.json').read_text())
    def select(n,other):
        a=ext[n]
        if other not in ext: return a,np.full(a.shape,n)
        b=ext[other]
        mask=lambda arr:cv2.morphologyEx((arr>0).astype('u1'),cv2.MORPH_CLOSE,np.ones((21,21),'u1'))
        use=cv2.distanceTransform(mask(a),cv2.DIST_L2,3)>=cv2.distanceTransform(mask(b),cv2.DIST_L2,3)
        return np.where(use,a,b),np.where(use,n,other)
    west,wcam=select(IDS[1],COMPANIONS[1]);east,ecam=select(IDS[2],COMPANIONS[0])
    for n,arr,target,cam in [(IDS[0],ext[IDS[0]],west,None),(IDS[1],west,None,wcam),(IDS[2],east,regd['postH'],ecam),(IDS[3],ext[IDS[3]],regd['pre18'],None)]:
        flow=None if target is None else reg(arr,target,return_flow=True)[2]
        for k,(x,y) in SITES.items():
            pt=np.array([x,y])+(flow[y,x] if flow is not None else 0)
            name=n if cam is None else cam[int(round(pt[1])),int(round(pt[0]))]
            affine=np.array(stats[name]['affine']);sx,sy=np.linalg.solve(affine[:,:2],pt-affine[:,2]); sample,line=raw_pixel(sx,sy,inputs[name]);lon,lat=forward_map(x,y)
            rows.append(dict(site=k,product=name+'.IMG',kind='PDS detector',east_deg=lon,north_deg=lat,sample=sample,line=line))
    df=pd.DataFrame(rows);df.to_csv(D/'image-coordinates.csv',index=False)
    print(df.query("site=='NW' and kind=='PDS detector'").round(3).to_string(index=False))
if __name__=="__main__":
    with threadpool_limits(limits=4):main()
