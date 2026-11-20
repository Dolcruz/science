"""Compare local stereo disparities from all three 25 December 2025 views."""
from field import *
SITES={"NW":(229,360,5.5),"NNE":(665,359,8.),"adjacent_NW":(220,358,5.5),"NE":(1081,287,5.5)}
def crops():
    east=geotiff('NAC_DTM_NEW200CRAT3_M1521338586_100cm_crop.tif')
    west=geotiff('ortho')
    with np.load(D/"registered.npz") as reg:z=reg['postM']
    def img(a):
        h=log(a);h=h-blur(h,16)
        return np.uint8(np.clip(128+h*150,0,255))
    return {"E":img(east),"N":img(z),"W":img(west)}
def paths(sx,sy):
    lon,lat=np.radians(forward_map(sx,sy))
    east=np.array([-np.sin(lon),np.cos(lon),0])
    north=np.array([-np.sin(lat)*np.cos(lon),-np.sin(lat)*np.sin(lon),np.cos(lat)])
    up=np.cross(east,north)
    result={}
    for key,v in json.loads((D/"stereo-geometry.json").read_text()).items():
        slat,slon=np.radians([v["sub_lat"],v["sub_lon"]])
        sat=(1737.4+v["altitude_km"])*np.array([np.cos(slat)*np.cos(slon),np.cos(slat)*np.sin(slon),np.sin(slat)])
        result[key]=np.array([-sat@east,sat@north])/(sat@up-(1737.4-.846))
    return result
def solve():
    ref=crops();out=[];allmaps={}
    fig,axes=plt.subplots(len(SITES),5,figsize=(13,2.55*len(SITES)))
    for rr,(site,(sx,sy,rad)) in enumerate(SITES.items()):
        const=paths(sx,sy)
        half=23; yy,xx=np.mgrid[-half:half+1,-half:half+1];r=np.hypot(xx,yy)
        p=np.float32(np.c_[xx.ravel()+sx,yy.ravel()+sy]).reshape(-1,1,2); ring=(r>=.8*rad)&(r<=1.3*rad);center=r<.31*rad
        fields={}
        for a,b in [('E','W'),('E','N'),('N','W')]:
            for width in [5,7,9,11,15]:
                q,ok1,_=cv2.calcOpticalFlowPyrLK(ref[a],ref[b],p,None,winSize=(width,width),maxLevel=2,minEigThreshold=.00006)
                back,ok2,_=cv2.calcOpticalFlowPyrLK(ref[b],ref[a],q,None,winSize=(width,width),maxLevel=2,minEigThreshold=.00006)
                delta=(q[:,0]-p[:,0]).reshape(*xx.shape,2)
                back_err=np.linalg.norm(back[:,0]-p[:,0],axis=1).reshape(xx.shape)
                good=(ok1[:,0]>0).reshape(xx.shape)&(ok2[:,0]>0).reshape(xx.shape)&(back_err<.35)
                bg=(r>rad*1.55)&(r<half)&good
                mat=np.stack([np.ones(r.shape),xx,yy],axis=-1)
                direction=const[b]-const[a]
                yz=(delta[:,:,1]*direction[0]-delta[:,:,0]*direction[1])/np.linalg.norm(direction)
                if bg.sum()<4:continue
                ref_y=mat@np.linalg.lstsq(mat[bg],yz[bg],rcond=None)[0]
                good&=abs(yz-ref_y)<.65
                h=(delta@direction)/(direction@direction)
                good_bg=bg&good
                if np.sum(good_bg)<4:continue
                h-=mat@np.linalg.lstsq(mat[good_bg],h[good_bg],rcond=None)[0]
                h[~good]=np.nan
                vals=lambda mask:float(np.nanmedian(h[mask])) if np.isfinite(h[mask]).any() else np.nan
                zc=vals(center);zr=vals(ring)
                quad=[]
                for c in [(xx<=0)&(yy<=0),(xx>=0)&(yy<=0),(xx>=0)&(yy>=0),(xx<=0)&(yy>=0)]:quad.append(vals(ring&c)-zc)
                out.append(dict(site=site,x=sx,y=sy,method=a+b,window=width,valid_center=int((center&good).sum()),center_minus_annulus=zc-zr,
                                rim_above_center_NW=quad[0],rim_above_center_NE=quad[1],
                                rim_above_center_SE=quad[2],rim_above_center_SW=quad[3],
                                center_fb_error=float(np.nanmedian(back_err[center]))))
                if width==7:fields[a+b]=h.copy();allmaps[site+'_'+a+b]=h
        dtm=geotiff("dtm")[sy-half:sy+half+1,sx-half:sx+half+1].copy()
        bg=(r>rad*1.55)&(r<half);dtm-=mat@np.linalg.lstsq(mat[bg],dtm[bg],rcond=None)[0]
        ext=[-half-.5,half+.5,half+.5,-half-.5]
        raw=ref["N"][sy-half:sy+half+1,sx-half:sx+half+1]
        for ax,(key,img) in zip(axes[rr],[('nadir',raw),('DTM',dtm),('E–N',fields.get('EN')),('N–W',fields.get('NW')),('E–W',fields.get('EW'))]):
            if img is None:continue
            ax.imshow(img,extent=ext,cmap='gray' if key=='nadir' else 'RdBu_r',vmin=50 if key=='nadir' else -1.2,vmax=208 if key=='nadir' else 1.2)
            ax.add_patch(plt.Circle((0,0),rad,fill=False,lw=.7,color='limegreen'));ax.set_xticks([-15,0,15]);ax.set_yticks([-15,0,15]);ax.set_title(key,fontsize=9)
        axes[rr,0].set_ylabel(f'{site}\n({sx}, {sy})',fontsize=9)
    fig.suptitle("Relative stereo relief around candidate sites  •  1 m grid  •  residual heights in ±1.2 m",fontsize=13)
    fig.tight_layout();fig.savefig(D/'stereo-maps.png',dpi=145);plt.close(fig)
    t=pd.DataFrame(out);t.to_csv(D/'stereo-apertures.csv',index=False);np.savez_compressed(D/'stereo-apertures.npz',**allmaps)
    print(t.query('window in [5,7,9]').pivot_table(index=['site','method'],columns='window',values='center_minus_annulus').round(2).to_string())
if __name__=="__main__":
    with threadpool_limits(limits=4):solve()
